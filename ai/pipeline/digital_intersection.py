"""
Digital Intersection State View & Simulation Engine.

Provides a unified real-time 4-approach junction model:
- 4 approaches: North, South, East, West.
- Signal phase tracking: Green, Yellow, All-Red clearance.
- Per-approach traffic statistics (vehicles, queues, PCE, priority, camera health).
- Remaining clearance / green countdown timers.
- Safety invariant enforcement: mutual exclusion, yellow clearance, all-red intervals,
  camera dropout handling, and AI stall safety fallback.
- Simulation stepping capability for offline verification, testing, and live replay.
"""

from dataclasses import dataclass, field
from enum import Enum
import math
import time
from typing import Dict, Any, Optional, List

from core.application_context import ApplicationContext
from ai.signal.signal_types import LaneName, PriorityResult, PriorityScore, PriorityBreakdown
from ai.signal.signal_decision import SignalDecision
from ai.signal.signal_scheduler import SignalScheduler
from ai.signal.priority_calculator import PriorityCalculator
from ai.analytics.analytics_exporter import LaneStatistics
from config.signal import MIN_GREEN_SEC, MAX_GREEN_SEC, YELLOW_SEC, ALL_RED_SEC
from ai.utils.logger import get_logger

logger = get_logger("DigitalIntersection")

APPROACH_NAMES = ["north", "east", "south", "west"]


class SignalColor(str, Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


class SafetyStatus(str, Enum):
    NORMAL = "NORMAL"
    ALL_RED_HOLD = "ALL_RED_HOLD"
    DEGRADED = "DEGRADED"


@dataclass
class ApproachState:
    vehicles: int = 0
    queue: int = 0
    pce: float = 0.0
    priority: float = 0.0
    camera_status: str = "OFFLINE"  # "HEALTHY" | "DEGRADED" | "OFFLINE"
    signal: SignalColor = SignalColor.RED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vehicles": self.vehicles,
            "queue": self.queue,
            "pce": round(self.pce, 2),
            "priority": round(self.priority, 2),
            "camera_status": self.camera_status,
            "signal": self.signal.value if isinstance(self.signal, Enum) else str(self.signal),
        }


class DigitalIntersection:
    """
    4-approach digital intersection state machine and snapshot provider.
    Can operate against live ApplicationContext or in standalone simulation mode.
    """

    def __init__(
        self,
        context: Optional[ApplicationContext] = None,
        simulation_mode: bool = False,
        min_green_sec: int = MIN_GREEN_SEC,
        max_green_sec: int = MAX_GREEN_SEC,
        yellow_sec: int = YELLOW_SEC,
        all_red_sec: int = ALL_RED_SEC,
    ):
        self.context = context
        self.simulation_mode = simulation_mode
        self.min_green_sec = min_green_sec
        self.max_green_sec = max_green_sec
        self.yellow_sec = yellow_sec
        self.all_red_sec = all_red_sec

        # Scheduler & priority engines for simulation or fallback
        self.sim_scheduler = SignalScheduler(
            min_green_sec=self.min_green_sec,
            max_green_sec=self.max_green_sec,
            yellow_sec=self.yellow_sec,
        )
        self.sim_calculator = PriorityCalculator()

        # Simulation state
        self.sim_phase_state: str = "ALL_RED"  # "GREEN" | "YELLOW" | "ALL_RED"
        self.sim_active_lane: Optional[str] = None
        self.sim_remaining_sec: float = 0.0
        self.sim_cycle_count: int = 0
        self.sim_lanes_served_in_cycle: set = set()
        self.sim_ai_stalled: bool = False
        self.sim_camera_status: Dict[str, str] = {lane: "HEALTHY" for lane in APPROACH_NAMES}
        self.sim_stats: Dict[str, LaneStatistics] = {
            lane: LaneStatistics(lane_name=lane, live_count=0, raw_count=0)
            for lane in APPROACH_NAMES
        }
        self.sim_last_priority_scores: Dict[str, float] = {lane: 0.0 for lane in APPROACH_NAMES}

        logger.info(
            f"DigitalIntersection initialized (simulation_mode={simulation_mode}, "
            f"min_green={min_green_sec}s, max_green={max_green_sec}s, "
            f"yellow={yellow_sec}s, all_red={all_red_sec}s)"
        )

    def trigger_camera_dropout(self, lane_name: str, status: str = "OFFLINE") -> None:
        """Simulate a camera disconnection or dropout on a specific approach."""
        lane_key = lane_name.lower()
        if lane_key in self.sim_camera_status:
            self.sim_camera_status[lane_key] = status
            # If the currently active green approach drops out, force immediate yellow clearance
            if self.sim_active_lane == lane_key and self.sim_phase_state == "GREEN":
                logger.warning(f"Active green camera '{lane_key}' dropped out; initiating yellow clearance.")
                self.sim_phase_state = "YELLOW"
                self.sim_remaining_sec = float(self.yellow_sec)

    def trigger_ai_stall(self, stalled: bool = True) -> None:
        """Simulate or report AI pipeline stall; forces fail-safe ALL_RED_HOLD."""
        self.sim_ai_stalled = stalled
        if stalled:
            logger.warning("AI stall triggered in DigitalIntersection; enforcing ALL_RED_HOLD.")
            self.sim_phase_state = "ALL_RED"
            self.sim_active_lane = None
            self.sim_remaining_sec = 0.0

    def step_simulation(
        self,
        dt: float = 1.0,
        lane_demands: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Advance simulation clock by dt seconds under optional traffic demand updates.

        Args:
            dt: Elapsed time in seconds.
            lane_demands: Optional map of lane_name -> {
                "vehicles": int, "queue": int, "pce": float, "has_priority": bool
            }
        """
        # 1. Update lane statistics if demand provided
        if lane_demands:
            for lane, demand in lane_demands.items():
                lane_key = lane.lower()
                if lane_key in self.sim_stats:
                    raw_count = demand.get("vehicles", self.sim_stats[lane_key].raw_count)
                    queue_count = demand.get("queue", self.sim_stats[lane_key].stopped_count)
                    pce = float(demand.get("pce", self.sim_stats[lane_key].pce_score))
                    has_priority = bool(demand.get("has_priority", self.sim_stats[lane_key].has_priority_vehicle))

                    self.sim_stats[lane_key] = LaneStatistics(
                        lane_name=lane_key,
                        live_count=raw_count,
                        raw_count=raw_count,
                        stopped_count=queue_count,
                        pce_score=pce,
                        has_priority_vehicle=has_priority,
                    )

        # 2. Check for AI stall or all cameras offline -> ALL_RED_HOLD
        all_cameras_offline = all(s == "OFFLINE" for s in self.sim_camera_status.values())
        if self.sim_ai_stalled or all_cameras_offline:
            self.sim_phase_state = "ALL_RED"
            self.sim_active_lane = None
            self.sim_remaining_sec = 0.0
            return self._build_sim_snapshot()

        # 3. Compute priority scores for active fresh cameras
        active_fresh = [
            l for l, s in self.sim_camera_status.items()
            if s != "OFFLINE"
        ]
        priority_res = self.sim_calculator.calculate(self.sim_stats)
        for s in priority_res.scores:
            lane_k = getattr(s.lane, "value", str(s.lane)).lower()
            self.sim_last_priority_scores[lane_k] = s.score

        # 4. State Machine Progression
        if self.sim_phase_state == "GREEN":
            self.sim_remaining_sec -= dt
            if self.sim_remaining_sec <= 0:
                # Transition GREEN -> YELLOW
                self.sim_phase_state = "YELLOW"
                self.sim_remaining_sec = float(self.yellow_sec)

        elif self.sim_phase_state == "YELLOW":
            self.sim_remaining_sec -= dt
            if self.sim_remaining_sec <= 0:
                # Transition YELLOW -> ALL_RED
                self.sim_phase_state = "ALL_RED"
                self.sim_remaining_sec = float(self.all_red_sec)

        elif self.sim_phase_state == "ALL_RED":
            self.sim_remaining_sec = max(0.0, self.sim_remaining_sec - dt)
            if self.sim_remaining_sec <= 0:
                # Clearance elapsed: select next approach with demand
                eligible_res, _ = self.sim_scheduler.select_eligible(
                    priority_res, self.sim_stats, set(active_fresh)
                )
                if eligible_res and eligible_res.highest_priority:
                    winner = eligible_res.highest_priority
                    winner_lane = getattr(winner.lane, "value", str(winner.lane)).lower()
                    decision = self.sim_scheduler.schedule(eligible_res)

                    self.sim_active_lane = winner_lane
                    self.sim_phase_state = "GREEN"
                    self.sim_remaining_sec = float(decision.green_duration_sec)

                    if winner_lane in self.sim_lanes_served_in_cycle or len(self.sim_lanes_served_in_cycle) >= 4:
                        self.sim_cycle_count += 1
                        self.sim_lanes_served_in_cycle = {winner_lane}
                    else:
                        self.sim_lanes_served_in_cycle.add(winner_lane)
                        if len(self.sim_lanes_served_in_cycle) == 4:
                            self.sim_cycle_count += 1
                            self.sim_lanes_served_in_cycle.clear()
                else:
                    # No demand or no fresh cameras; stay in ALL_RED
                    self.sim_active_lane = None
                    self.sim_phase_state = "ALL_RED"
                    self.sim_remaining_sec = 0.0

        return self._build_sim_snapshot()

    def _build_sim_snapshot(self) -> Dict[str, Any]:
        """Format simulation state into the standardized API snapshot."""
        approaches: Dict[str, Dict[str, Any]] = {}

        # Determine signals per approach
        for lane in APPROACH_NAMES:
            cam_status = self.sim_camera_status.get(lane, "OFFLINE")
            stat = self.sim_stats.get(lane)
            vehicles = stat.raw_count if stat else 0
            queue = stat.stopped_count if stat else 0
            pce = stat.pce_score if stat else 0.0
            priority = self.sim_last_priority_scores.get(lane, 0.0)

            if self.sim_phase_state == "GREEN" and self.sim_active_lane == lane:
                sig = SignalColor.GREEN
            elif self.sim_phase_state == "YELLOW" and self.sim_active_lane == lane:
                sig = SignalColor.YELLOW
            else:
                sig = SignalColor.RED

            approaches[lane] = ApproachState(
                vehicles=vehicles,
                queue=queue,
                pce=pce,
                priority=priority,
                camera_status=cam_status,
                signal=sig,
            ).to_dict()

        # Determine active phase string and current lanes
        current_green_lane = None
        current_yellow_lane = None
        active_phase = "all_red"

        if self.sim_phase_state == "GREEN" and self.sim_active_lane:
            current_green_lane = self.sim_active_lane
            active_phase = f"{self.sim_active_lane}_green"
        elif self.sim_phase_state == "YELLOW" and self.sim_active_lane:
            current_yellow_lane = self.sim_active_lane
            active_phase = f"{self.sim_active_lane}_yellow"
        else:
            active_phase = "all_red"

        # Determine safety status
        if self.sim_ai_stalled or all(s == "OFFLINE" for s in self.sim_camera_status.values()):
            safety_status = SafetyStatus.ALL_RED_HOLD.value
        elif any(s != "HEALTHY" for s in self.sim_camera_status.values()):
            safety_status = SafetyStatus.DEGRADED.value
        else:
            safety_status = SafetyStatus.NORMAL.value

        return {
            "timestamp": round(time.time(), 3),
            "active_phase": active_phase,
            "current_green_lane": current_green_lane,
            "current_yellow_lane": current_yellow_lane,
            "remaining_time_seconds": max(0, int(math.ceil(self.sim_remaining_sec))),
            "approaches": approaches,
            "safety_status": safety_status,
            "cycle_count": self.sim_cycle_count,
        }

    def get_snapshot(self) -> Dict[str, Any]:
        """
        Return the real-time or simulated 4-approach digital intersection snapshot.
        If running live with an active TrafficPipeline, inspects live context.
        Otherwise, returns deterministic simulation/safe fallback state.
        """
        if self.simulation_mode:
            return self._build_sim_snapshot()

        ctx = self.context or ApplicationContext.get_instance()

        # Check if live pipeline is present and running
        pipeline = getattr(ctx, "pipeline", None)
        if pipeline is None or not ctx.system_running:
            # Safe default / hold state before camera connection or when system stopped
            return self._get_safe_hold_snapshot(ctx)

        now_mono = time.monotonic()
        decision: Optional[SignalDecision] = getattr(pipeline, "active_decision", None)
        phase_start: float = getattr(pipeline, "phase_start_time", 0.0)
        elapsed_sec = (now_mono - phase_start) if phase_start > 0 else 999.0

        # Camera health per approach (fresh if seen in last 3s)
        camera_statuses: Dict[str, str] = {}
        for lane in APPROACH_NAMES:
            last_seen = ctx.lane_last_seen.get(lane, 0.0)
            camera_statuses[lane] = "HEALTHY" if (now_mono - last_seen < 3.0) else "OFFLINE"

        # AI stall check
        ai_stalled = bool(
            ctx.is_pipeline_stalled
            or (now_mono - ctx.last_frame_monotonic > 5.0 and len(ctx.frame_updated_at) > 0)
        )

        # Signal state determination
        current_green_lane = None
        current_yellow_lane = None
        active_phase = "all_red"
        remaining_time_sec = 0

        if decision and not ai_stalled:
            green_lane_str = getattr(decision.green_lane, "value", str(decision.green_lane)).lower()
            green_dur = decision.green_duration_sec
            yellow_dur = decision.yellow_duration_sec
            all_red_dur = self.all_red_sec

            if elapsed_sec < green_dur:
                current_green_lane = green_lane_str
                active_phase = f"{green_lane_str}_green"
                remaining_time_sec = max(0, int(math.ceil(green_dur - elapsed_sec)))
            elif elapsed_sec < (green_dur + yellow_dur):
                current_yellow_lane = green_lane_str
                active_phase = f"{green_lane_str}_yellow"
                remaining_time_sec = max(0, int(math.ceil(green_dur + yellow_dur - elapsed_sec)))
            else:
                active_phase = "all_red"
                remaining_time_sec = max(0, int(math.ceil(green_dur + yellow_dur + all_red_dur - elapsed_sec)))

        # Priority scores map
        priority_scores: Dict[str, float] = {}
        if getattr(pipeline, "last_priority_result", None):
            for s in pipeline.last_priority_result.scores:
                lane_k = getattr(s.lane, "value", str(s.lane)).lower()
                priority_scores[lane_k] = s.score

        # Build approach states
        approaches: Dict[str, Dict[str, Any]] = {}
        for lane in APPROACH_NAMES:
            cam_stat = camera_statuses.get(lane, "OFFLINE")
            lane_stat: Optional[LaneStatistics] = ctx.lane_stats_history.get(lane)
            vehicles = lane_stat.raw_count if lane_stat else 0
            queue = lane_stat.stopped_count if lane_stat else 0
            pce = lane_stat.pce_score if lane_stat else 0.0
            priority = priority_scores.get(lane, 0.0)

            if current_green_lane == lane:
                sig = SignalColor.GREEN
            elif current_yellow_lane == lane:
                sig = SignalColor.YELLOW
            else:
                sig = SignalColor.RED

            approaches[lane] = ApproachState(
                vehicles=vehicles,
                queue=queue,
                pce=pce,
                priority=priority,
                camera_status=cam_stat,
                signal=sig,
            ).to_dict()

        # Safety status evaluation
        if ai_stalled or all(s == "OFFLINE" for s in camera_statuses.values()):
            safety_status = SafetyStatus.ALL_RED_HOLD.value
        elif any(s != "HEALTHY" for s in camera_statuses.values()):
            safety_status = SafetyStatus.DEGRADED.value
        else:
            safety_status = SafetyStatus.NORMAL.value

        phase_counter = getattr(pipeline, "phase_counter", 0)
        cycle_count = phase_counter // 4

        return {
            "timestamp": round(time.time(), 3),
            "active_phase": active_phase,
            "current_green_lane": current_green_lane,
            "current_yellow_lane": current_yellow_lane,
            "remaining_time_seconds": remaining_time_sec,
            "approaches": approaches,
            "safety_status": safety_status,
            "cycle_count": cycle_count,
        }

    def _get_safe_hold_snapshot(self, ctx: ApplicationContext) -> Dict[str, Any]:
        """Safe default snapshot when no cameras are connected or system is stopped."""
        now_mono = time.monotonic()
        camera_statuses = {
            lane: "HEALTHY" if (now_mono - ctx.lane_last_seen.get(lane, 0.0) < 3.0) else "OFFLINE"
            for lane in APPROACH_NAMES
        }
        has_any_fresh = any(s == "HEALTHY" for s in camera_statuses.values())

        approaches = {
            lane: ApproachState(
                vehicles=0,
                queue=0,
                pce=0.0,
                priority=0.0,
                camera_status=camera_statuses[lane],
                signal=SignalColor.RED,
            ).to_dict()
            for lane in APPROACH_NAMES
        }

        return {
            "timestamp": round(time.time(), 3),
            "active_phase": "all_red",
            "current_green_lane": None,
            "current_yellow_lane": None,
            "remaining_time_seconds": 0,
            "approaches": approaches,
            "safety_status": SafetyStatus.ALL_RED_HOLD.value if not has_any_fresh else SafetyStatus.DEGRADED.value,
            "cycle_count": 0,
        }
