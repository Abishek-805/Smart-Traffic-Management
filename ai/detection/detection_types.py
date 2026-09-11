"""
Data structures representing detection outputs in standard format.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, Optional, Dict, Any


class ObservationState(str, Enum):
    """Whether a box is detector evidence or display-only tracker projection."""

    OBSERVED = "OBSERVED"
    PREDICTED = "PREDICTED"


@dataclass
class Detection:
    """
    Immutable representation of a single detected object in a frame,
    enriched as it flows through tracking, lane assignment, and state management.
    """
    class_name: str
    class_id: int
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    track_id: Optional[int] = None
    lane: Optional[str] = None
    motion_px_sec: float = 0.0
    time_in_lane_sec: float = 0.0
    queue_time_sec: float = 0.0
    is_priority: bool = False
    frame_number: int = 0
    timestamp: float = 0.0
    extra_metadata: Dict[str, Any] = field(default_factory=dict)
    observation_type: ObservationState = ObservationState.OBSERVED

    @property
    def centroid(self) -> Tuple[int, int]:
        """Calculate center point of bounding box (x, y)."""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize detection object to dict for logging or JSON serialization.
        """
        return {
            "id": self.track_id,
            "class": self.class_name,
            "class_id": self.class_id,
            "confidence": round(self.confidence, 4),
            "bbox": list(self.bbox),
            "centroid": list(self.centroid),
            "lane": self.lane,
            "motion_px_sec": round(self.motion_px_sec, 2),
            "time_in_lane_sec": round(self.time_in_lane_sec, 1),
            "queue_time_sec": round(self.queue_time_sec, 1),
            "is_priority": self.is_priority,
            "frame_number": self.frame_number,
            "timestamp": round(self.timestamp, 3),
            "observation_type": self.observation_type.value,
        }
