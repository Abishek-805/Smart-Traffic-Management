"""
EmergencyOverride module for granting immediate priority green signals to emergency vehicles (ambulances, fire trucks).
"""

from enum import Enum
import time
from typing import Dict, List, Optional, Union

from ai.signal.signal_types import (
    LaneName,
    DecisionReason,
    PriorityBreakdown,
    PriorityScore,
    PriorityResult,
)
from ai.analytics.analytics_exporter import LaneStatistics
from config.signal import EMERGENCY_BOOST_SCORE
from ai.utils.logger import get_logger

logger = get_logger("EmergencyOverride")


class EmergencyOverride:
    """
    Inspects traffic analytics and priority results for priority/emergency vehicles.
    If detected, boosts the emergency lane score and moves it to Rank #1.
    """

    def __init__(self, boost_score: float = EMERGENCY_BOOST_SCORE):
        self.boost_score = boost_score
        logger.info(f"EmergencyOverride initialized with boost score: {self.boost_score}")

    def check_and_override(
        self,
        priority_result: PriorityResult,
        lane_stats: Optional[Dict[str, LaneStatistics]] = None,
    ) -> PriorityResult:
        """
        Check for emergency vehicles in traffic analytics or priority results.
        
        Args:
            priority_result (PriorityResult): Current PriorityResult object.
            lane_stats (Optional[Dict[str, LaneStatistics]]): Analytics stats mapping.
            
        Returns:
            PriorityResult: Overridden or unchanged PriorityResult payload.
        """
        if not priority_result or not priority_result.scores:
            return priority_result

        emergency_lanes: List[str] = []

        # 1. Check LaneStatistics for has_priority_vehicle flag
        if lane_stats:
            for lane_name_str, stats in lane_stats.items():
                if stats.has_priority_vehicle:
                    emergency_lanes.append(str(lane_name_str).lower())

        # 2. If emergency lane identified, grant override
        if not emergency_lanes:
            return priority_result

        logger.warning(
            f"🚨 EMERGENCY VEHICLE DETECTED in lane(s): {emergency_lanes}! "
            f"Granting immediate priority green override."
        )

        overridden_scores: List[PriorityScore] = []

        for score_obj in priority_result.scores:
            lane_str = score_obj.lane.value if isinstance(score_obj.lane, Enum) else str(score_obj.lane)
            
            if lane_str.lower() in emergency_lanes:
                # Apply emergency boost
                boosted_total = round(score_obj.score + self.boost_score, 2)
                
                bd = score_obj.breakdown
                updated_bd = PriorityBreakdown(
                    pce=bd.pce,
                    queue=bd.queue,
                    congestion=bd.congestion,
                    fairness_bonus=bd.fairness_bonus,
                    raw_pce=bd.raw_pce,
                    raw_queue_sec=bd.raw_queue_sec,
                    raw_congestion_index=bd.raw_congestion_index,
                )

                boosted_obj = PriorityScore(
                    lane=score_obj.lane,
                    score=boosted_total,
                    rank=0,
                    breakdown=updated_bd,
                )
                overridden_scores.append(boosted_obj)
            else:
                overridden_scores.append(score_obj)

        # Re-sort scores descending
        overridden_scores.sort(key=lambda s: s.score, reverse=True)

        # Re-assign ranks
        for rank_idx, s in enumerate(overridden_scores, start=1):
            s.rank = rank_idx

        highest = overridden_scores[0] if overridden_scores else None

        return PriorityResult(
            scores=overridden_scores,
            highest_priority=highest,
            timestamp=priority_result.timestamp or time.time(),
        )
