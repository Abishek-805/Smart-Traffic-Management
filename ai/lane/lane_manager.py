"""
LaneManager module for defining ROI polygons and assigning vehicles to lanes.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import cv2
import numpy as np

from ai.detection.detection_types import Detection
from ai.utils.logger import get_logger

logger = get_logger("LaneManager")


@dataclass
class Lane:
    """
    Extensible representation of an intersection lane.
    """
    name: str
    polygon: np.ndarray  # Points array of shape (N, 2)
    direction: str = "Straight"
    priority: int = 1
    signal_group: str = "Group_1"


class LaneManager:
    """
    Manages lane definitions using a normalized (0.0–1.0) coordinate system.
    Polygons are stored as fractional coordinates and scaled to pixel space
    on demand, making them resolution-independent for any incoming frame size.
    """

    def __init__(self, frame_width: int = 1280, frame_height: int = 720):
        self.frame_width = frame_width if frame_width > 0 else 1280
        self.frame_height = frame_height if frame_height > 0 else 720
        self.lanes: Dict[str, Lane] = {}

        # Normalized polygon definitions (0.0–1.0 coordinate space).
        # These are derived from the canonical 4-quadrant junction layout and
        # work for ANY resolution — 640×360, 720p, 1080p, future IP cameras.
        self._normalized_polygons: Dict[str, np.ndarray] = {
            # North (Top trapezoid): full top edge → converging to centre strip
            "North": np.array([
                [0.0, 0.0],
                [1.0, 0.0],
                [0.6, 0.5],
                [0.4, 0.5],
            ], dtype=np.float32),

            # South (Bottom trapezoid): centre strip → full bottom edge
            "South": np.array([
                [0.4, 0.5],
                [0.6, 0.5],
                [1.0, 1.0],
                [0.0, 1.0],
            ], dtype=np.float32),

            # West (Left wedge): left edge → centre strip
            "West": np.array([
                [0.0, 0.0],
                [0.5, 0.4],
                [0.5, 0.6],
                [0.0, 1.0],
            ], dtype=np.float32),

            # East (Right wedge): centre strip → right edge
            "East": np.array([
                [1.0, 0.0],
                [0.5, 0.4],
                [0.5, 0.6],
                [1.0, 1.0],
            ], dtype=np.float32),
        }

        self._build_lanes(self.frame_width, self.frame_height)

    def _build_lanes(self, width: int, height: int) -> None:
        """
        Build Lane objects by scaling normalized polygon definitions to pixel
        coordinates for the given resolution.
        """
        self.lanes = {
            "North": Lane(
                "North",
                self._scale_polygon(self._normalized_polygons["North"], width, height),
                direction="Southbound", priority=1, signal_group="Phase_A",
            ),
            "South": Lane(
                "South",
                self._scale_polygon(self._normalized_polygons["South"], width, height),
                direction="Northbound", priority=1, signal_group="Phase_A",
            ),
            "West": Lane(
                "West",
                self._scale_polygon(self._normalized_polygons["West"], width, height),
                direction="Eastbound", priority=1, signal_group="Phase_B",
            ),
            "East": Lane(
                "East",
                self._scale_polygon(self._normalized_polygons["East"], width, height),
                direction="Westbound", priority=1, signal_group="Phase_B",
            ),
        }
        logger.info(
            f"LaneManager initialized with 4 lanes covering {width}x{height} resolution: "
            f"{list(self.lanes.keys())}"
        )

    @staticmethod
    def _scale_polygon(normalized: np.ndarray, width: int, height: int) -> np.ndarray:
        """Scale a normalized (0–1) polygon to pixel coordinates."""
        scale = np.array([width, height], dtype=np.float32)
        return (normalized * scale).astype(np.int32)

    def get_scaled_polygons(self, frame_width: int, frame_height: int) -> Dict[str, np.ndarray]:
        """
        Return pixel-coordinate polygons scaled to the given frame dimensions.
        No internal state is mutated — safe to call every frame with any resolution.
        """
        return {
            name: self._scale_polygon(norm_poly, frame_width, frame_height)
            for name, norm_poly in self._normalized_polygons.items()
        }

    def assign_lanes(
        self,
        detections: List[Detection],
        frame_width: Optional[int] = None,
        frame_height: Optional[int] = None,
    ) -> List[Detection]:
        """
        Evaluate centroid of each vehicle against lane ROI polygons and assign det.lane.

        If frame_width / frame_height are supplied, polygons are scaled on the fly to
        those dimensions — resolution-independent, no rebuild required.
        """
        w = frame_width if frame_width and frame_width > 0 else self.frame_width
        h = frame_height if frame_height and frame_height > 0 else self.frame_height

        scaled_polygons = self.get_scaled_polygons(w, h)

        for det in detections:
            cx, cy = det.centroid
            point = (float(cx), float(cy))
            assigned_lane = None

            for lane_name, polygon in scaled_polygons.items():
                res = cv2.pointPolygonTest(polygon, point, measureDist=False)
                if res >= 0:
                    assigned_lane = lane_name
                    break

            # Fallback: assign nearest quadrant based on normalized centroid position
            if assigned_lane is None:
                assigned_lane = self._get_fallback_quadrant(cx, cy, w, h)

            det.lane = assigned_lane

        return detections

    def _get_fallback_quadrant(self, cx: int, cy: int, width: int, height: int) -> str:
        """Assign lane by simple midpoint quadrant fallback if outside ROI polygons."""
        mid_x = width / 2.0
        mid_y = height / 2.0

        dx = cx - mid_x
        dy = cy - mid_y

        if abs(dx) > abs(dy):
            return "East" if dx > 0 else "West"
        else:
            return "South" if dy > 0 else "North"
