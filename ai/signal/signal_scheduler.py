"""
SignalScheduler engine for converting PriorityResult objects into SignalDecision phase allocations.
Uses ratio-based adaptive green-time allocation clamped within configurable bounds.
"""

from typing import List, Optional
import time

from ai.signal.signal_types import (
    LaneName,
    DecisionReason,
    PriorityScore,
    PriorityResult,
)
from ai.signal.signal_decision import SignalDecision
from config.signal import MIN_GREEN_SEC, MAX_GREEN_SEC, YELLOW_SEC
from ai.utils.logger import get_logger

logger = get_logger("SignalScheduler")


class SignalScheduler:
    """
    Schedules traffic light phase decisions based on input PriorityResult rankings.
    Independent of vision models, camera hardware, and ESP32 communications.
    """

    def __init__(
        self,
        min_green_sec: int = MIN_GREEN_SEC,
        max_green_sec: int = MAX_GREEN_SEC,
        yellow_sec: int = YELLOW_SEC,
    ):
        self.min_green_sec = min_green_sec
        self.max_green_sec = max_green_sec
        self.yellow_sec = yellow_sec
        logger.info(
            f"SignalScheduler initialized (Min Green: {self.min_green_sec}s, "
            f"Max Green: {self.max_green_sec}s, Yellow: {self.yellow_sec}s)"
        )

    def schedule(self, priority_result: PriorityResult, phase_id: int = 1) -> SignalDecision:
        """
        Public API method to schedule a traffic light phase decision.
        
        Args:
            priority_result (PriorityResult): Validated container holding lane priority scores.
            phase_id (int): Monotonic sequential phase ID.
            
        Returns:
            SignalDecision: Strongly-typed decision payload.
            
        Raises:
            ValueError: If priority_result is None or contains no scores.
        """
        if not priority_result or not priority_result.scores:
            logger.error("Schedule called with empty or None PriorityResult.")
            raise ValueError("PriorityResult must not be None and must contain at least one score.")

        # Step 1: Select Green Lane Winner
        winner = self._select_green_lane(priority_result)

        # Step 2: Calculate Adaptive Green Duration
        green_duration_sec = self._calculate_green_time(winner, priority_result)

        # Step 3: Construct SignalDecision Object
        decision = self._build_decision(winner, green_duration_sec, priority_result, phase_id)

        # Log concise cycle summary
        green_str = winner.lane.value if hasattr(winner.lane, "value") else str(winner.lane)
        reason_str = decision.reason.value if hasattr(decision.reason, "value") else str(decision.reason)
        logger.info(
            f"[Scheduler Phase #{phase_id}] Winner: {green_str:<6} | Score: {winner.score:<5.2f} | "
            f"Green: {green_duration_sec}s | Reason: {reason_str}"
        )

        return decision

    def select_eligible(self, result, lane_stats, fresh_lanes, waiting_cycles, max_wait_cycles=3):
        """Do not serve stale/empty approaches while fresh demand exists.
        After a bounded number of completed phases, serve the oldest waiting
        demand even if its weighted score is smaller than a busy approach.
        """
        key = lambda score: getattr(score.lane, "value", str(score.lane)).lower()
        demand = [s for s in result.scores if key(s) in fresh_lanes and lane_stats.get(key(s)) and lane_stats[key(s)].raw_count > 0]
        eligible = demand or [s for s in result.scores if key(s) in fresh_lanes]
        if not eligible:
            return None, False
        emergency = [s for s in demand if lane_stats[key(s)].has_priority_vehicle]
        if emergency:
            result.highest_priority = max(emergency, key=lambda s: s.score)
            return result, False
        overdue = [s for s in demand if waiting_cycles.get(getattr(s.lane, "value", str(s.lane)), 0) >= max_wait_cycles]
        winner = max(overdue, key=lambda s: (waiting_cycles.get(getattr(s.lane, "value", str(s.lane)), 0), s.score)) if overdue else max(eligible, key=lambda s: s.score)
        result.highest_priority = winner
        return result, bool(overdue)

    def _select_green_lane(self, priority_result: PriorityResult) -> PriorityScore:
        """
        Select winner lane with highest priority score in O(1) time.
        """
        winner = priority_result.highest_priority
        if not winner:
            winner = priority_result.scores[0]
        return winner

    def _calculate_green_time(self, winner: PriorityScore, priority_result: PriorityResult) -> int:
        """
        Calculate adaptive green duration based on winner score ratio relative to total junction priority.
        
        Formula:
            ratio = winner_score / total_junction_score
            green_time = MIN_GREEN + ratio * (MAX_GREEN - MIN_GREEN)
        """
        total_score_sum = sum(max(0.0, s.score) for s in priority_result.scores)

        # Edge case: All zero scores or non-positive total
        if total_score_sum <= 0 or winner.score <= 0:
            return self.min_green_sec

        # Compute winner ratio
        ratio = max(0.0, winner.score) / total_score_sum

        # Calculate adaptive duration
        raw_duration = self.min_green_sec + (ratio * (self.max_green_sec - self.min_green_sec))
        calculated_green = int(round(raw_duration))

        # Clamp duration strictly within [MIN_GREEN_SEC, MAX_GREEN_SEC]
        clamped_green = max(self.min_green_sec, min(self.max_green_sec, calculated_green))
        return clamped_green

    def _build_decision(
        self,
        winner: PriorityScore,
        green_duration_sec: int,
        priority_result: PriorityResult,
        phase_id: int,
    ) -> SignalDecision:
        """
        Construct strongly-typed SignalDecision payload.
        """
        red_lanes = [s.lane for s in priority_result.scores if s.lane != winner.lane]
        winner_str = winner.lane.value if hasattr(winner.lane, "value") else str(winner.lane)

        return SignalDecision(
            phase_id=phase_id,
            green_lane=winner.lane,
            green_duration_sec=green_duration_sec,
            yellow_duration_sec=self.yellow_sec,
            red_lanes=red_lanes,
            priority_score=winner.score,
            reason=DecisionReason.NORMAL,
            reason_details=f"Highest weighted priority score ({winner.score:.2f}) for lane '{winner_str}'.",
            timestamp=priority_result.timestamp or time.time(),
        )
