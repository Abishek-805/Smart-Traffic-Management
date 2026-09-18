"""
Traffic and Video Replay Lab.
Provides reproducible multi-camera traffic simulation, stress testing,
and scenario regression verification across synthetic and recorded traffic profiles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from ai.signal.signal_types import (
    LaneName,
    DecisionReason,
    PriorityBreakdown,
    PriorityScore,
    PriorityResult,
)
from ai.signal.signal_decision import SignalDecision
from ai.signal.signal_scheduler import SignalScheduler
from ai.analytics.analytics_exporter import LaneStatistics


class TrafficScenario(str, Enum):
    """Standard traffic simulation scenarios."""
    BALANCED_NORMAL = "BALANCED_NORMAL"
    HEAVY_NORTH = "HEAVY_NORTH"
    ALL_BUSY_GRIDLOCK = "ALL_BUSY_GRIDLOCK"
    CAMERA_DISCONNECT = "CAMERA_DISCONNECT"
    EMERGENCY_PREEMPTION = "EMERGENCY_PREEMPTION"
    SUDDEN_SPIKE = "SUDDEN_SPIKE"


@dataclass
class ReplayStepRecord:
    """Telemetry captured for one step of the replay simulation."""
    step_index: int
    active_green_lane: str
    green_duration_sec: int
    yellow_duration_sec: int
    reason: str
    decision_details: str
    lane_counts: Dict[str, int]
    lane_pce: Dict[str, float]
    lane_queues: Dict[str, float]
    priority_scores: Dict[str, float]
    timestamp: float


@dataclass
class ReplayRunResult:
    """Consolidated result of a scenario replay execution."""
    scenario_name: str
    total_steps: int
    steps: List[ReplayStepRecord] = field(default_factory=list)
    green_allocations_by_lane: Dict[str, int] = field(default_factory=lambda: {"north": 0, "south": 0, "east": 0, "west": 0})
    emergency_preemptions: int = 0
    disconnected_dropouts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario": self.scenario_name,
            "total_steps": self.total_steps,
            "green_allocations": self.green_allocations_by_lane,
            "emergency_preemptions": self.emergency_preemptions,
            "disconnected_dropouts": self.disconnected_dropouts,
            "step_count": len(self.steps),
        }


class TrafficReplayLab:
    """
    Simulates intersection traffic flows under controlled scenario dynamics
    and measures scheduler responses, fairness, and safety invariants.
    """

    def __init__(
        self,
        min_green: int = 10,
        max_green: int = 60,
        yellow_sec: int = 3,
    ):
        self.scheduler = SignalScheduler(
            min_green_sec=min_green,
            max_green_sec=max_green,
            yellow_sec=yellow_sec,
        )

    def run_scenario(
        self,
        scenario: TrafficScenario | str,
        total_steps: int = 12,
    ) -> ReplayRunResult:
        """
        Execute a multi-step traffic replay scenario.
        """
        scenario_name = scenario.value if isinstance(scenario, TrafficScenario) else str(scenario)
        result = ReplayRunResult(scenario_name=scenario_name, total_steps=total_steps)

        # Re-initialize scheduler state
        self.scheduler = SignalScheduler(
            min_green_sec=self.scheduler.min_green_sec,
            max_green_sec=self.scheduler.max_green_sec,
            yellow_sec=self.scheduler.yellow_sec,
        )

        sim_time = 1000.0

        for step in range(total_steps):
            lane_stats, fresh_lanes = self._generate_scenario_traffic(scenario_name, step)
            priority_result = self._calculate_priority(lane_stats, fresh_lanes)

            # Check for camera dropout
            if len(fresh_lanes) < 4:
                result.disconnected_dropouts += (4 - len(fresh_lanes))

            # Schedule next green allocation
            eligible_result, _ = self.scheduler.select_eligible(
                priority_result,
                lane_stats,
                fresh_lanes,
            )

            if eligible_result and eligible_result.highest_priority:
                winner = eligible_result.highest_priority
                green_time = self.scheduler._calculate_green_time(winner, eligible_result)
                decision = self.scheduler._build_decision(winner, green_time, eligible_result, phase_id=step + 1)
                green_lane_str = getattr(decision.green_lane, "value", str(decision.green_lane)).lower()
                result.green_allocations_by_lane[green_lane_str] = (
                    result.green_allocations_by_lane.get(green_lane_str, 0) + 1
                )
                if lane_stats.get(green_lane_str) and lane_stats[green_lane_str].has_priority_vehicle:
                    result.emergency_preemptions += 1
            else:
                # All lanes empty or stale -> default clearance/fallback
                decision = SignalDecision(
                    phase_id=step + 1,
                    green_lane=LaneName.NORTH,
                    green_duration_sec=self.scheduler.min_green_sec,
                    yellow_duration_sec=self.scheduler.yellow_sec,
                    red_lanes=[LaneName.SOUTH, LaneName.EAST, LaneName.WEST],
                    priority_score=0.0,
                    reason=DecisionReason.ALL_RED_FALLBACK,
                    reason_details="No fresh demand; maintaining safe fallback",
                    timestamp=sim_time,
                )
                green_lane_str = "north"

            record = ReplayStepRecord(
                step_index=step,
                active_green_lane=green_lane_str,
                green_duration_sec=decision.green_duration_sec,
                yellow_duration_sec=decision.yellow_duration_sec,
                reason=getattr(decision.reason, "value", str(decision.reason)),
                decision_details=decision.reason_details,
                lane_counts={k: s.raw_count for k, s in lane_stats.items()},
                lane_pce={k: s.pce_score for k, s in lane_stats.items()},
                lane_queues={k: s.total_queue_time_sec for k, s in lane_stats.items()},
                priority_scores={getattr(s.lane, "value", str(s.lane)).lower(): s.score for s in priority_result.scores},
                timestamp=sim_time,
            )
            result.steps.append(record)
            sim_time += decision.green_duration_sec + decision.yellow_duration_sec + 2.0  # +2s all-red

        return result

    def _generate_scenario_traffic(
        self,
        scenario: str,
        step: int,
    ) -> Tuple[Dict[str, LaneStatistics], List[str]]:
        """Generate approach loads for the given scenario and step."""
        lanes = ["north", "south", "east", "west"]
        fresh_lanes = list(lanes)
        stats: Dict[str, LaneStatistics] = {}

        if scenario == TrafficScenario.BALANCED_NORMAL.value:
            for l in lanes:
                stats[l] = LaneStatistics(
                    lane_name=l, live_count=5, raw_count=5, pce_score=5.0,
                    stopped_count=2, total_queue_time_sec=15.0,
                )

        elif scenario == TrafficScenario.HEAVY_NORTH.value:
            stats["north"] = LaneStatistics(
                lane_name="north", live_count=18, raw_count=18, pce_score=24.0,
                stopped_count=12, total_queue_time_sec=110.0,
            )
            for l in ["south", "east", "west"]:
                stats[l] = LaneStatistics(
                    lane_name=l, live_count=2, raw_count=2, pce_score=2.0,
                    stopped_count=1, total_queue_time_sec=5.0,
                )

        elif scenario == TrafficScenario.ALL_BUSY_GRIDLOCK.value:
            for l in lanes:
                stats[l] = LaneStatistics(
                    lane_name=l, live_count=15, raw_count=15, pce_score=20.0,
                    stopped_count=10, total_queue_time_sec=90.0,
                )

        elif scenario == TrafficScenario.CAMERA_DISCONNECT.value:
            # East camera disconnects after step 3
            if step > 3:
                fresh_lanes.remove("east")
            for l in lanes:
                stats[l] = LaneStatistics(
                    lane_name=l, live_count=4, raw_count=4, pce_score=4.0,
                    stopped_count=1, total_queue_time_sec=10.0,
                )

        elif scenario == TrafficScenario.EMERGENCY_PREEMPTION.value:
            # Ambulance appears on South at step 2
            is_emergency = (step >= 2)
            for l in lanes:
                stats[l] = LaneStatistics(
                    lane_name=l, live_count=6, raw_count=6, pce_score=6.0,
                    stopped_count=2, total_queue_time_sec=20.0,
                    has_priority_vehicle=(l == "south" and is_emergency),
                )

        elif scenario == TrafficScenario.SUDDEN_SPIKE.value:
            # West has sudden massive influx at step 4
            west_count = 20 if step >= 4 else 1
            stats["west"] = LaneStatistics(
                lane_name="west", live_count=west_count, raw_count=west_count,
                pce_score=west_count * 1.2, stopped_count=west_count // 2,
                total_queue_time_sec=west_count * 5.0,
            )
            for l in ["north", "south", "east"]:
                stats[l] = LaneStatistics(
                    lane_name=l, live_count=3, raw_count=3, pce_score=3.0,
                    stopped_count=1, total_queue_time_sec=10.0,
                )
        else:
            for l in lanes:
                stats[l] = LaneStatistics(lane_name=l, live_count=1, raw_count=1)

        return stats, fresh_lanes

    def _calculate_priority(
        self,
        lane_stats: Dict[str, LaneStatistics],
        fresh_lanes: List[str],
    ) -> PriorityResult:
        """Compute PriorityResult container matching SignalScheduler expectations."""
        scores = []
        name_map = {
            "north": LaneName.NORTH,
            "south": LaneName.SOUTH,
            "east": LaneName.EAST,
            "west": LaneName.WEST,
        }
        for l_name, enum_val in name_map.items():
            st = lane_stats.get(l_name)
            if not st or l_name not in fresh_lanes:
                score_val = 0.0
                breakdown = PriorityBreakdown(pce=0.0, queue=0.0, congestion=0.0, raw_pce=0.0, raw_queue_sec=0.0)
            else:
                if st.has_priority_vehicle:
                    score_val = 1000.0
                else:
                    score_val = st.pce_score * 0.45 + (st.total_queue_time_sec / 10.0) * 0.35 + st.stopped_count * 0.20
                breakdown = PriorityBreakdown(
                    pce=st.pce_score,
                    queue=st.total_queue_time_sec,
                    congestion=float(st.stopped_count),
                    raw_pce=st.pce_score,
                    raw_queue_sec=st.total_queue_time_sec,
                )
            scores.append(PriorityScore(lane=enum_val, score=score_val, rank=1, breakdown=breakdown))

        scores.sort(key=lambda s: s.score, reverse=True)
        for i, s in enumerate(scores):
            s.rank = i + 1

        return PriorityResult(scores=scores, highest_priority=scores[0] if scores else None)
