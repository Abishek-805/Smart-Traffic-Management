"""
Ground-Plane Homography & Metric Queue Calibration module.
Transforms 2D image plane coordinates [u, v] into real-world metric road coordinates [X, Y] (meters)
to estimate physical queue length and road occupancy accurately.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np


@dataclass(frozen=True)
class QueueMetrics:
    """Queue length and density estimates with calibration provenance."""
    queued_count: int
    pixel_queue_length: float
    metric_queue_length_meters: float
    is_calibrated: bool
    farthest_vehicle_id: Optional[int] = None


class HomographyCalibrator:
    """
    Computes and applies a perspective transformation matrix (Homography)
    mapping camera image pixels to ground-plane metric coordinates (meters).
    """

    def __init__(
        self,
        image_points: np.ndarray,
        metric_points: np.ndarray,
        stop_line_metric_y: float = 0.0,
    ):
        """
        Args:
            image_points: 4x2 array of image pixel points [(u1, v1), (u2, v2), (u3, v3), (u4, v4)].
            metric_points: 4x2 array of corresponding road coordinates in meters [(X1, Y1), (X2, Y2), ...].
            stop_line_metric_y: Metric Y position of the stop line (meters, typically 0.0).
        """
        if len(image_points) != 4 or len(metric_points) != 4:
            raise ValueError("Exactly 4 point correspondences required to compute homography.")

        src = np.asarray(image_points, dtype=np.float32)
        dst = np.asarray(metric_points, dtype=np.float32)

        self.H = cv2.getPerspectiveTransform(src, dst)
        self.H_inv = np.linalg.inv(self.H)
        self.stop_line_metric_y = stop_line_metric_y

    def pixel_to_metric(self, u: float, v: float) -> Tuple[float, float]:
        """Transform image coordinates (u, v) into ground-plane road coordinates (X, Y) in meters."""
        vec = np.array([u, v, 1.0], dtype=np.float64)
        dst_vec = self.H @ vec
        if abs(dst_vec[2]) < 1e-9:
            return 0.0, 0.0
        x_m = dst_vec[0] / dst_vec[2]
        y_m = dst_vec[1] / dst_vec[2]
        return float(x_m), float(y_m)

    def metric_to_pixel(self, x_m: float, y_m: float) -> Tuple[float, float]:
        """Inverse transform: ground-plane coordinates in meters to image pixels."""
        vec = np.array([x_m, y_m, 1.0], dtype=np.float64)
        src_vec = self.H_inv @ vec
        if abs(src_vec[2]) < 1e-9:
            return 0.0, 0.0
        u = src_vec[0] / src_vec[2]
        v = src_vec[1] / src_vec[2]
        return float(u), float(v)

    def compute_queue_length(
        self,
        queued_vehicle_centroids: List[Tuple[float, float]],
    ) -> float:
        """
        Calculate the metric queue length (meters) from the stop line to the farthest queued vehicle.
        """
        if not queued_vehicle_centroids:
            return 0.0

        distances = []
        for u, v in queued_vehicle_centroids:
            x_m, y_m = self.pixel_to_metric(u, v)
            dist_from_stop = abs(y_m - self.stop_line_metric_y)
            distances.append(dist_from_stop)

        return float(max(distances)) if distances else 0.0


class ApproachCalibrationManager:
    """
    Manages approach-specific camera calibrations (North, South, East, West).
    Provides seamless fallback to pixel-based approximations when uncalibrated.
    """

    def __init__(self, default_pixel_scale_m_per_px: float = 0.05):
        """
        Args:
            default_pixel_scale_m_per_px: Fallback scale when homography is uncalibrated (~5cm/pixel).
        """
        self.calibrators: Dict[str, HomographyCalibrator] = {}
        self.default_pixel_scale = default_pixel_scale_m_per_px

    def set_calibration(
        self,
        approach: str,
        image_points: np.ndarray,
        metric_points: np.ndarray,
        stop_line_metric_y: float = 0.0,
    ) -> None:
        """Register a 4-point homography calibration for an approach."""
        key = approach.strip().lower()
        self.calibrators[key] = HomographyCalibrator(
            image_points=image_points,
            metric_points=metric_points,
            stop_line_metric_y=stop_line_metric_y,
        )

    def estimate_queue(
        self,
        approach: str,
        queued_vehicles: List[Dict[str, Any]],
        stop_line_pixel_y: float = 650.0,
    ) -> QueueMetrics:
        """
        Estimate queue count and metric queue length for an approach.
        
        Args:
            approach: 'north', 'south', 'east', or 'west'.
            queued_vehicles: List of dicts with 'centroid' (u, v) and optional 'track_id'.
            stop_line_pixel_y: Fallback pixel Y position of the stop line.
        """
        key = approach.strip().lower()
        count = len(queued_vehicles)
        if count == 0:
            return QueueMetrics(
                queued_count=0,
                pixel_queue_length=0.0,
                metric_queue_length_meters=0.0,
                is_calibrated=key in self.calibrators,
                farthest_vehicle_id=None,
            )

        calibrator = self.calibrators.get(key)
        centroids = [tuple(v["centroid"]) for v in queued_vehicles if "centroid" in v]

        # Calculate pixel distance
        pixel_dists = [abs(c[1] - stop_line_pixel_y) for c in centroids]
        max_pixel_dist = float(max(pixel_dists)) if pixel_dists else 0.0

        if calibrator is not None:
            metric_length = calibrator.compute_queue_length(centroids)
            is_calibrated = True
        else:
            metric_length = max_pixel_dist * self.default_pixel_scale
            is_calibrated = False

        # Find farthest vehicle track_id
        farthest_idx = int(np.argmax(pixel_dists)) if pixel_dists else None
        farthest_id = queued_vehicles[farthest_idx].get("track_id") if farthest_idx is not None else None

        return QueueMetrics(
            queued_count=count,
            pixel_queue_length=round(max_pixel_dist, 1),
            metric_queue_length_meters=round(metric_length, 2),
            is_calibrated=is_calibrated,
            farthest_vehicle_id=farthest_id,
        )
