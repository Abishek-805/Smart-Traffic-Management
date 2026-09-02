"""
OccupancyAnalyzer computes live lane counts and PCE weighted road space occupancy scores.
"""

from typing import Dict, List, Any
from ai.state.vehicle_state_manager import VehicleState
from config.traffic import PCE_WEIGHTS


class OccupancyAnalyzer:
    """
    Analyzes live vehicle counts and computes Passenger Car Equivalent (PCE) weighted scores.
    """

    def __init__(self, pce_weights: Dict[str, float] = PCE_WEIGHTS):
        self.pce_weights = pce_weights

    def analyze(self, lane_vehicles: List[VehicleState]) -> Dict[str, Any]:
        """
        Analyze live vehicle states for a single lane.
        
        Returns:
            Dict containing live vehicle category counts, total count, and weighted PCE score.
        """
        counts = {
            "car": 0,
            "bus": 0,
            "truck": 0,
            "motorcycle": 0,
            "bicycle": 0,
        }
        pce_score = 0.0

        for state in lane_vehicles:
            category = state.class_name.lower()
            if category in counts:
                counts[category] += 1
            else:
                counts[category] = 1

            weight = self.pce_weights.get(category, 1.0)
            pce_score += weight

        total_live = len(lane_vehicles)

        return {
            "counts": counts,
            "total_live": total_live,
            "pce_score": round(pce_score, 2),
        }
