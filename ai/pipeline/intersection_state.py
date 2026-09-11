"""
IntersectionState and LaneProcessingResult data structures representing strongly-typed
per-lane perception results and unified intersection-wide state telemetry.
"""

from dataclasses import dataclass, field
import time
from typing import Dict, List, Optional, Any
import numpy as np

from ai.detection.detection_types import Detection
from ai.analytics.analytics_exporter import LaneStatistics


@dataclass
class LaneProcessingResult:
    """
    Per-camera lane processing result encapsulating detections, tracking, analytics, and frame.
    """
    lane_name: str
    raw_frame: Optional[np.ndarray] = None
    annotated_frame: Optional[np.ndarray] = None
    detections: List[Detection] = field(default_factory=list)
    statistics: Optional[LaneStatistics] = None
    connected: bool = True
    fps: Optional[float] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class IntersectionState:
    """
    Unified multi-lane intersection state telemetry passed to the Signal Decision Engine.
    """
    lanes: Dict[str, LaneStatistics] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    total_vehicles: int = 0
    active_phase_id: int = 0
    green_lane: Optional[str] = None
    remaining_green_sec: int = 0

    def get_lane_stats(self) -> Dict[str, LaneStatistics]:
        """Return dictionary mapping lane_name -> LaneStatistics for Decision Engine calculations."""
        return self.lanes
