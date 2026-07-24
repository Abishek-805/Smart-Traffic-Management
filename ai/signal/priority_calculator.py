"""
PriorityCalculator engine for ranking intersection lanes based on weighted traffic metrics.
Calculates base priority scores with transparent score breakdowns, ranks, and returns PriorityResult.
"""

import time
from enum import Enum
from typing import Dict, List, Optional
from ai.signal.signal_types import LaneName, PriorityBreakdown, PriorityScore, PriorityResult
from ai.analytics.analytics_exporter import LaneStatistics
from config.signal import PRIORITY_WEIGHTS
from ai.utils.logger import get_logger

logger = get_logger("PriorityCalculator")


class PriorityCalculator:
    """
    Computes base priority scores for intersection lanes using normalized configurable weights.
    Outputs strongly-typed PriorityResult containers with rank order and transparent breakdowns.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        raw_weights = weights or PRIORITY_WEIGHTS
        self.weights = self._normalize_weights(raw_weights)
        logger.info(f"PriorityCalculator initialized with normalized weights: {self.weights}")

    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Validate and normalize priority weights so they sum to 1.0.
        """
        total = sum(weights.values())
        if total <= 0:
            logger.warning("Invalid priority weights sum <= 0. Falling back to default (0.45, 0.35, 0.20).")
            return {"pce": 0.45, "queue": 0.35, "congestion": 0.20}
        
        return {k: round(v / total, 4) for k, v in weights.items()}

    def calculate(self, lane_stats: Dict[str, LaneStatistics]) -> PriorityResult:
        """
        Calculate base priority scores and ranks for all lanes in the statistics dictionary.
        
        Args:
            lane_stats: Dictionary mapping lane names to LaneStatistics objects.
            
        Returns:
            PriorityResult: Container holding sorted PriorityScore objects, top priority, and timestamp.
        """
        unranked_scores: List[PriorityScore] = []

        w_pce = self.weights.get("pce", 0.45)
        w_queue = self.weights.get("queue", 0.35)
        w_congestion = self.weights.get("congestion", 0.20)

        for lane_name_str, stats in lane_stats.items():
            try:
                lane_enum = LaneName(lane_name_str)
            except ValueError:
                lane_enum = lane_name_str

            # 1. Component Score Contributions
            pce_contrib = w_pce * stats.pce_score
            queue_contrib = w_queue * stats.total_queue_time_sec
            congestion_contrib = w_congestion * stats.congestion_index

            # 2. Total Base Priority Score
            total_score = pce_contrib + queue_contrib + congestion_contrib

            # 3. Strongly Typed Score Breakdown
            breakdown = PriorityBreakdown(
                pce=round(pce_contrib, 2),
                queue=round(queue_contrib, 2),
                congestion=round(congestion_contrib, 2),
                raw_pce=stats.pce_score,
                raw_queue_sec=stats.total_queue_time_sec,
                raw_congestion_index=stats.congestion_index,
            )

            # Assign temporary rank=0 before sorting
            score_obj = PriorityScore(
                lane=lane_enum,
                score=round(total_score, 2),
                rank=0,
                breakdown=breakdown,
            )
            unranked_scores.append(score_obj)

        # 4. Sort by priority score descending
        unranked_scores.sort(key=lambda s: s.score, reverse=True)

        # 5. Assign 1-indexed ranks and log calculations
        sorted_scores: List[PriorityScore] = []
        for rank_idx, score_obj in enumerate(unranked_scores, start=1):
            score_obj.rank = rank_idx
            sorted_scores.append(score_obj)

            lane_str = score_obj.lane.value if isinstance(score_obj.lane, Enum) else str(score_obj.lane)
            bd = score_obj.breakdown
            logger.info(
                f"[Rank #{rank_idx}] Lane: {lane_str:<6} | PCE: {bd.pce:<5.2f} | "
                f"Queue: {bd.queue:<5.2f} | Congestion: {bd.congestion:<5.2f} | Total: {score_obj.score:.2f}"
            )

        highest = sorted_scores[0] if sorted_scores else None

        return PriorityResult(
            scores=sorted_scores,
            highest_priority=highest,
            timestamp=time.time(),
        )
