"""
AnalyticsExporter produces strongly-typed LaneStatistics dataclass objects and JSON payloads.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any
import json

from ai.state.vehicle_state_manager import VehicleStateManager, VehicleState
from ai.analytics.occupancy_analyzer import OccupancyAnalyzer
from ai.analytics.congestion_analyzer import CongestionAnalyzer
from ai.utils.logger import get_logger

logger = get_logger("AnalyticsExporter")


@dataclass
class LaneStatistics:
    """
    Strongly-typed analytics object representing real-time metrics for a single lane.
    Phase 3.5: Added raw_count and smoothed_count for scheduler stabilization.
    """
    lane_name: str
    live_count: int = 0
    pce_score: float = 0.0
    stopped_count: int = 0
    total_queue_time_sec: float = 0.0
    max_queue_time_sec: float = 0.0
    avg_motion_px_sec: float = 0.0
    congestion_index: float = 0.0
    density: str = "LOW"
    historical_count: int = 0
    has_priority_vehicle: bool = False
    vehicle_breakdown: Dict[str, int] = field(default_factory=dict)
    # Phase 3.5 — Stabilization fields
    raw_count: int = 0          # Unfiltered live_count snapshot before smoothing
    smoothed_count: float = 0.0  # EMA-smoothed vehicle count passed to scheduler

    def to_dict(self) -> Dict[str, Any]:
        """Convert LaneStatistics to dictionary format."""
        return {
            "lane": self.lane_name,
            "live_count": self.live_count,
            "pce_score": self.pce_score,
            "stopped_count": self.stopped_count,
            "queue_time_sec": self.total_queue_time_sec,
            "max_queue_time_sec": self.max_queue_time_sec,
            "avg_motion_px_sec": self.avg_motion_px_sec,
            "congestion_index": self.congestion_index,
            "density": self.density,
            "historical_count": self.historical_count,
            "priority": self.has_priority_vehicle,
            "breakdown": self.vehicle_breakdown,
            "raw_count": self.raw_count,
            "smoothed_count": round(self.smoothed_count, 2),
        }


class AnalyticsExporter:
    """
    Orchestrates OccupancyAnalyzer and CongestionAnalyzer to generate LaneStatistics records.
    """

    def __init__(self):
        self.occupancy_analyzer = OccupancyAnalyzer()
        self.congestion_analyzer = CongestionAnalyzer()

    def generate_stats(self, state_manager: VehicleStateManager) -> Dict[str, LaneStatistics]:
        """
        Generate LaneStatistics objects for all active lanes.
        """
        grouped_vehicles = state_manager.get_active_vehicles_by_lane()
        all_lanes = ["North", "South", "East", "West"]
        
        lane_stats: Dict[str, LaneStatistics] = {}

        for lane_name in all_lanes:
            vehicles = grouped_vehicles.get(lane_name, [])
            
            # Occupancy Analysis
            occ_res = self.occupancy_analyzer.analyze(vehicles)
            
            # Congestion Analysis
            cong_res = self.congestion_analyzer.analyze(vehicles, occ_res["pce_score"])
            
            # Historical cumulative count
            hist_count = len(state_manager.historical_tracks_count.get(lane_name, set()))

            stats_obj = LaneStatistics(
                lane_name=lane_name,
                live_count=occ_res["total_live"],
                pce_score=occ_res["pce_score"],
                stopped_count=cong_res["stopped_count"],
                total_queue_time_sec=cong_res["total_queue_time_sec"],
                max_queue_time_sec=cong_res["max_queue_time_sec"],
                avg_motion_px_sec=cong_res["avg_motion_px_sec"],
                congestion_index=cong_res["congestion_index"],
                density=cong_res["density"],
                historical_count=hist_count,
                has_priority_vehicle=cong_res["has_priority_vehicle"],
                vehicle_breakdown=occ_res["counts"],
                raw_count=occ_res["total_live"],  # Phase 3.5: snapshot raw count
            )
            lane_stats[lane_name] = stats_obj

        return lane_stats

    def export_json(self, lane_stats: Dict[str, LaneStatistics]) -> str:
        """
        Export LaneStatistics to JSON format ready for Sprint 3 adaptive signal engine.
        """
        data = {lane: stats.to_dict() for lane, stats in lane_stats.items()}
        return json.dumps(data, indent=2)
