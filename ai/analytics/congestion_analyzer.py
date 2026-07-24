"""
CongestionAnalyzer calculates queue metrics, average motion, and Congestion Index.
"""

from typing import Dict, List, Any
from ai.state.vehicle_state_manager import VehicleState
from config.traffic import CONGESTION_WEIGHTS, DENSITY_THRESHOLDS


class CongestionAnalyzer:
    """
    Evaluates traffic congestion indices and queue metrics per lane.
    """

    def __init__(
        self,
        congestion_weights: Dict[str, float] = CONGESTION_WEIGHTS,
        density_thresholds: Dict[str, float] = DENSITY_THRESHOLDS,
    ):
        self.weights = congestion_weights
        self.thresholds = density_thresholds

    def analyze(self, lane_vehicles: List[VehicleState], pce_score: float) -> Dict[str, Any]:
        """
        Analyze queue times, motion speeds, and compute Congestion Index for a single lane.
        """
        if not lane_vehicles:
            return {
                "stopped_count": 0,
                "total_queue_time_sec": 0.0,
                "max_queue_time_sec": 0.0,
                "avg_motion_px_sec": 0.0,
                "congestion_index": 0.0,
                "density": "LOW",
                "has_priority_vehicle": False,
            }

        stopped_count = 0
        total_queue_time = 0.0
        max_queue_time = 0.0
        total_motion = 0.0
        has_priority = False

        for state in lane_vehicles:
            total_motion += state.motion_px_sec
            if state.is_priority:
                has_priority = True

            if state.is_queued or state.queue_time_sec > 0:
                stopped_count += 1
                total_queue_time += state.queue_time_sec
                if state.queue_time_sec > max_queue_time:
                    max_queue_time = state.queue_time_sec

        avg_motion = total_motion / len(lane_vehicles)

        # Configurable Congestion Index calculation formula
        congestion_index = (
            (self.weights.get("pce", 1.0) * pce_score)
            + (self.weights.get("queue_time", 0.2) * total_queue_time)
            + (self.weights.get("stopped", 5.0) * stopped_count)
        )

        density = self._classify_density(congestion_index)

        return {
            "stopped_count": stopped_count,
            "total_queue_time_sec": round(total_queue_time, 1),
            "max_queue_time_sec": round(max_queue_time, 1),
            "avg_motion_px_sec": round(avg_motion, 2),
            "congestion_index": round(congestion_index, 2),
            "density": density,
            "has_priority_vehicle": has_priority,
        }

    def _classify_density(self, index: float) -> str:
        """Categorize Congestion Index into LOW, MEDIUM, HIGH, or CONGESTED."""
        if index < self.thresholds.get("LOW", 8.0):
            return "LOW"
        elif index < self.thresholds.get("MEDIUM", 18.0):
            return "MEDIUM"
        elif index < self.thresholds.get("HIGH", 30.0):
            return "HIGH"
        else:
            return "CONGESTED"
