"""
FairnessManager engine for preventing lane starvation by applying waiting cycle bonuses.
"""

from enum import Enum
import time
from typing import Dict, List, Optional, Union

from ai.signal.signal_types import (
    LaneName,
    PriorityBreakdown,
    PriorityScore,
    PriorityResult,
)
from config.signal import FAIRNESS_BONUS_PER_CYCLE, MAX_FAIRNESS_BONUS
from ai.utils.logger import get_logger

logger = get_logger("FairnessManager")


class FairnessManager:
    """
    Tracks cycles since each lane was last served and applies starvation prevention bonuses.
    Encapsulated: Takes PriorityResult -> Returns adjusted PriorityResult.
    """

    def __init__(
        self,
        bonus_per_cycle: float = FAIRNESS_BONUS_PER_CYCLE,
        max_bonus: float = MAX_FAIRNESS_BONUS,
    ):
        self.bonus_per_cycle = bonus_per_cycle
        self.max_fairness_bonus = max_bonus
        self.cycles_since_served: Dict[str, int] = {
            "North": 0,
            "South": 0,
            "East": 0,
            "West": 0,
        }
        logger.info(
            f"FairnessManager initialized (Bonus/cycle: {self.bonus_per_cycle}, Max Cap: {self.max_fairness_bonus})"
        )

    def apply_fairness(self, priority_result: PriorityResult) -> PriorityResult:
        """
        Apply starvation waiting bonuses to PriorityResult scores and return re-ranked PriorityResult.
        
        Args:
            priority_result: Raw PriorityResult containing base demand scores.
            
        Returns:
            PriorityResult: Adjusted and re-sorted PriorityResult object.
        """
        if not priority_result or not priority_result.scores:
            return priority_result

        adjusted_scores: List[PriorityScore] = []

        for base_score_obj in priority_result.scores:
            lane_str = base_score_obj.lane.value if isinstance(base_score_obj.lane, Enum) else str(base_score_obj.lane)
            wait_cycles = self.cycles_since_served.get(lane_str, 0)

            # Calculate capped starvation waiting bonus
            raw_bonus = float(wait_cycles * self.bonus_per_cycle)
            fairness_bonus = min(raw_bonus, self.max_fairness_bonus)
            adjusted_total = round(base_score_obj.score + fairness_bonus, 2)

            # Clone breakdown with fairness_bonus populated
            bd = base_score_obj.breakdown
            updated_breakdown = PriorityBreakdown(
                pce=bd.pce,
                queue=bd.queue,
                congestion=bd.congestion,
                fairness_bonus=round(fairness_bonus, 2),
                raw_pce=bd.raw_pce,
                raw_queue_sec=bd.raw_queue_sec,
                raw_congestion_index=bd.raw_congestion_index,
            )

            adj_obj = PriorityScore(
                lane=base_score_obj.lane,
                score=adjusted_total,
                rank=0,  # Assigned after sorting
                breakdown=updated_breakdown,
            )
            adjusted_scores.append(adj_obj)

        # Re-sort scores descending based on adjusted total score
        adjusted_scores.sort(key=lambda s: s.score, reverse=True)

        # Re-assign 1-indexed ranks and log adjustments
        for rank_idx, score_obj in enumerate(adjusted_scores, start=1):
            score_obj.rank = rank_idx
            lane_str = score_obj.lane.value if isinstance(score_obj.lane, Enum) else str(score_obj.lane)
            wait_cycles = self.cycles_since_served.get(lane_str, 0)
            if wait_cycles > 0:
                logger.info(
                    f"[Fairness] Lane: {lane_str:<6} | Base Score: {score_obj.score - score_obj.breakdown.fairness_bonus:.2f} | "
                    f"Wait Cycles: {wait_cycles} | Bonus: +{score_obj.breakdown.fairness_bonus:.2f} | Adjusted: {score_obj.score:.2f}"
                )

        highest = adjusted_scores[0] if adjusted_scores else None

        return PriorityResult(
            scores=adjusted_scores,
            highest_priority=highest,
            timestamp=priority_result.timestamp or time.time(),
        )

    def update_served(self, green_lane: Union[LaneName, str]) -> None:
        """
        Update wait cycle counters: Reset winner counter to 0 and increment waiting lanes.
        """
        green_str = green_lane.value if isinstance(green_lane, Enum) else str(green_lane)

        if green_str not in self.cycles_since_served:
            self.cycles_since_served[green_str] = 0

        for lane_name in list(self.cycles_since_served.keys()):
            if lane_name == green_str:
                self.cycles_since_served[lane_name] = 0
            else:
                self.cycles_since_served[lane_name] += 1

        logger.info(f"[Fairness Updated] Green: '{green_str}' (Reset to 0). Waiting cycles: {self.cycles_since_served}")
