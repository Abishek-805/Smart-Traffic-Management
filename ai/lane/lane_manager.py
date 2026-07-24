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
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.lanes: Dict[str, Lane] = {}

        self._setup_default_lanes(frame_width, frame_height)

    def _setup_default_lanes(self, width: int, height: int) -> None:
        """
        Setup default 4-quadrant junction ROI polygons:
        North, South, East, West.
        """
        w, h = width, height

        # North Polygon (Top quadrant)
        north_poly = np.array([
            [int(w * 0.25), 0],
            [int(w * 0.75), 0],
            [int(w * 0.65), int(h * 0.40)],
            [int(w * 0.35), int(h * 0.40)],
        ], dtype=np.int32)

        # South Polygon (Bottom quadrant)
        south_poly = np.array([
            [int(w * 0.35), int(h * 0.60)],
            [int(w * 0.65), int(h * 0.60)],
            [int(w * 0.75), h],
            [int(w * 0.25), h],
        ], dtype=np.int32)

        # West Polygon (Left quadrant)
        west_poly = np.array([
            [0, int(h * 0.20)],
            [int(w * 0.35), int(h * 0.40)],
            [int(w * 0.35), int(h * 0.60)],
            [0, int(h * 0.80)],
        ], dtype=np.int32)

        # East Polygon (Right quadrant)
        east_poly = np.array([
            [int(w * 0.65), int(h * 0.40)],
            [w, int(h * 0.20)],
            [w, int(h * 0.80)],
            [int(w * 0.65), int(h * 0.60)],
        ], dtype=np.int32)

        self.lanes = {
            "North": Lane("North", north_poly, direction="Southbound", priority=1, signal_group="Phase_A"),
            "South": Lane("South", south_poly, direction="Northbound", priority=1, signal_group="Phase_A"),
            "East": Lane("East", east_poly, direction="Westbound", priority=1, signal_group="Phase_B"),
            "West": Lane("West", west_poly, direction="Eastbound", priority=1, signal_group="Phase_B"),
        }
        logger.info(f"LaneManager initialized with {len(self.lanes)} lanes: {list(self.lanes.keys())}")

    def assign_lanes(self, detections: List[Detection]) -> List[Detection]:
        """
        Evaluate centroid of each vehicle against lane ROI polygons and assign det.lane.
        """
        for det in detections:
            cx, cy = det.centroid
            point = (float(cx), float(cy))
            assigned_lane = None

            for lane_name, lane in self.lanes.items():
                # cv2.pointPolygonTest returns >= 0 if inside or on edge
                res = cv2.pointPolygonTest(lane.polygon, point, measureDist=False)
                if res >= 0:
                    assigned_lane = lane_name
                    break

            # Fallback if vehicle is outside strict polygons: assign nearest polygon quadrant
            if assigned_lane is None:
                assigned_lane = self._get_fallback_quadrant(cx, cy)

            det.lane = assigned_lane

        return detections

    def _get_fallback_quadrant(self, cx: int, cy: int) -> str:
        """Assign lane by simple midpoint quadrant fallback if outside ROI polygons."""
        half_w = self.frame_width / 2.0
        half_h = self.frame_height / 2.0

        if cy < half_h:
            return "North" if cx < half_w else "East"
        else:
            return "West" if cx < half_w else "South"
