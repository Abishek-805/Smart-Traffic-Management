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
    Manages lane definitions and performs point-in-polygon geometric matching.
    """

    def __init__(self, frame_width: int = 1280, frame_height: int = 720):
        self.frame_width = frame_width if frame_width > 0 else 1280
        self.frame_height = frame_height if frame_height > 0 else 720
        self.lanes: Dict[str, Lane] = {}

        self._setup_default_lanes(self.frame_width, self.frame_height)

    def _setup_default_lanes(self, width: int, height: int) -> None:
        """
        Setup default 4-quadrant junction ROI polygons:
        North (Top), South (Bottom), West (Left), East (Right).
        """
        w, h = width, height
        cx, cy = w // 2, h // 2

        # North Polygon (Top triangular/trapezoidal quadrant)
        north_poly = np.array([
            [0, 0],
            [w, 0],
            [cx + int(w * 0.1), cy],
            [cx - int(w * 0.1), cy],
        ], dtype=np.int32)

        # South Polygon (Bottom triangular/trapezoidal quadrant)
        south_poly = np.array([
            [cx - int(w * 0.1), cy],
            [cx + int(w * 0.1), cy],
            [w, h],
            [0, h],
        ], dtype=np.int32)

        # West Polygon (Left quadrant)
        west_poly = np.array([
            [0, 0],
            [cx, cy - int(h * 0.1)],
            [cx, cy + int(h * 0.1)],
            [0, h],
        ], dtype=np.int32)

        # East Polygon (Right quadrant)
        east_poly = np.array([
            [w, 0],
            [cx, cy - int(h * 0.1)],
            [cx, cy + int(h * 0.1)],
            [w, h],
        ], dtype=np.int32)

        self.lanes = {
            "North": Lane("North", north_poly, direction="Southbound", priority=1, signal_group="Phase_A"),
            "South": Lane("South", south_poly, direction="Northbound", priority=1, signal_group="Phase_A"),
            "East": Lane("East", east_poly, direction="Westbound", priority=1, signal_group="Phase_B"),
            "West": Lane("West", west_poly, direction="Eastbound", priority=1, signal_group="Phase_B"),
        }
        logger.info(f"LaneManager initialized with 4 lanes covering {w}x{h} resolution: {list(self.lanes.keys())}")

    def assign_lanes(self, detections: List[Detection]) -> List[Detection]:
        """
        Evaluate centroid of each vehicle against lane ROI polygons and assign det.lane.
        """
        for det in detections:
            cx, cy = det.centroid
            point = (float(cx), float(cy))
            assigned_lane = None

            # Primary: Point-in-polygon check
            for lane_name, lane in self.lanes.items():
                res = cv2.pointPolygonTest(lane.polygon, point, measureDist=False)
                if res >= 0:
                    assigned_lane = lane_name
                    break

            # Fallback: Assign nearest quadrant based on centroid position relative to center
            if assigned_lane is None:
                assigned_lane = self._get_fallback_quadrant(cx, cy)

            det.lane = assigned_lane

        return detections

    def _get_fallback_quadrant(self, cx: int, cy: int) -> str:
        """Assign lane by simple midpoint quadrant fallback if outside ROI polygons."""
        mid_x = self.frame_width / 2.0
        mid_y = self.frame_height / 2.0

        dx = cx - mid_x
        dy = cy - mid_y

        # Compare horizontal vs vertical distance from center
        if abs(dx) > abs(dy):
            return "East" if dx > 0 else "West"
        else:
            return "South" if dy > 0 else "North"
