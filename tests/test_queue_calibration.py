"""
Tests for Ground-Plane Homography and Metric Queue Calibration.
"""

import numpy as np
import pytest
from ai.analytics.calibration import (
    HomographyCalibrator,
    ApproachCalibrationManager,
    QueueMetrics,
)


def test_homography_calibrator_transformation():
    # 4 points forming a trapezoid in perspective (e.g. road lane)
    # top width = 200px (far away), bottom width = 600px (near camera)
    src_pixels = np.array([
        [540, 200],   # Top-left (far left)
        [740, 200],   # Top-right (far right)
        [940, 700],   # Bottom-right (near right)
        [340, 700],   # Bottom-left (near left)
    ], dtype=np.float32)

    # In reality, this lane is a rectangle of 3.5m wide and 40m long
    # Origin (0,0) at stop-line center
    dst_metric = np.array([
        [-1.75, 40.0],  # Far left
        [1.75, 40.0],   # Far right
        [1.75, 0.0],    # Near right (stop line)
        [-1.75, 0.0],   # Near left (stop line)
    ], dtype=np.float32)

    calibrator = HomographyCalibrator(src_pixels, dst_metric, stop_line_metric_y=0.0)

    # Test stop line near bottom-left pixel
    x_m, y_m = calibrator.pixel_to_metric(340, 700)
    assert x_m == pytest.approx(-1.75, abs=0.05)
    assert y_m == pytest.approx(0.0, abs=0.05)

    # Test far top-right pixel
    x_m, y_m = calibrator.pixel_to_metric(740, 200)
    assert x_m == pytest.approx(1.75, abs=0.05)
    assert y_m == pytest.approx(40.0, abs=0.05)

    # Test inverse transformation (metric back to pixel)
    u, v = calibrator.metric_to_pixel(-1.75, 40.0)
    assert u == pytest.approx(540, abs=0.5)
    assert v == pytest.approx(200, abs=0.5)


def test_homography_queue_distance():
    src_pixels = np.array([
        [500, 100],
        [700, 100],
        [900, 600],
        [300, 600],
    ], dtype=np.float32)

    dst_metric = np.array([
        [-2.0, 50.0],
        [2.0, 50.0],
        [2.0, 0.0],
        [-2.0, 0.0],
    ], dtype=np.float32)

    calibrator = HomographyCalibrator(src_pixels, dst_metric, stop_line_metric_y=0.0)

    # Two queued vehicles: one at stop line (v=600), one 25 meters back
    # At 25m back, Y = 25m -> pixel v should be between 100 and 600
    mid_u, mid_v = calibrator.metric_to_pixel(0.0, 25.0)

    queue = [(600, 600), (mid_u, mid_v)]
    dist = calibrator.compute_queue_length(queue)

    assert dist == pytest.approx(25.0, abs=0.5)


def test_approach_calibration_manager_calibrated_vs_uncalibrated():
    manager = ApproachCalibrationManager(default_pixel_scale_m_per_px=0.1)

    # Register North calibration
    src_pixels = np.array([
        [500, 100], [700, 100], [900, 600], [300, 600]
    ], dtype=np.float32)
    dst_metric = np.array([
        [-2.0, 50.0], [2.0, 50.0], [2.0, 0.0], [-2.0, 0.0]
    ], dtype=np.float32)
    manager.set_calibration("north", src_pixels, dst_metric, stop_line_metric_y=0.0)

    vehicles = [
        {"track_id": 10, "centroid": (600, 580)},
        {"track_id": 11, "centroid": (600, 300)},
    ]

    # North approach is calibrated
    north_queue = manager.estimate_queue("north", vehicles, stop_line_pixel_y=600.0)
    assert north_queue.queued_count == 2
    assert north_queue.calibrated is True
    assert north_queue.unit == "metres"
    assert north_queue.value > 0.0
    assert north_queue.calibration_id is not None
    assert north_queue.metric_queue_length_meters > 0.0
    assert north_queue.farthest_vehicle_id == 11

    # South approach is uncalibrated -> reports image-space evidence only.
    south_queue = manager.estimate_queue("south", vehicles, stop_line_pixel_y=600.0)
    assert south_queue.queued_count == 2
    assert south_queue.calibrated is False
    assert south_queue.unit == "image_space"
    assert south_queue.value == pytest.approx(300.0, abs=0.1)
    assert south_queue.metric_queue_length_meters is None
    assert south_queue.calibration_id is None
    assert south_queue.farthest_vehicle_id == 11


def test_approach_calibration_empty_queue():
    manager = ApproachCalibrationManager()
    queue = manager.estimate_queue("east", [])
    assert queue.queued_count == 0
    assert queue.metric_queue_length_meters is None
    assert queue.pixel_queue_length == 0.0
    assert queue.farthest_vehicle_id is None
    assert queue.unit == "image_space"
    assert queue.metric_queue_length_meters is None
