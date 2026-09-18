"""
Golden-model regression tests for the active YOLOv8n model.

Verifies:
1. Reference asset availability and loadability.
2. Structural invariants (bounding boxes within frame, classes in target set, valid confidences).
3. Numerical stability invariants over multiple inference runs without strict bit-exact float equality.
4. Latency measurement reasonableness.
"""

from pathlib import Path
import cv2
import numpy as np
import pytest

from ai.detection.detector import VehicleDetector
from config.traffic import TARGET_CLASS_NAMES

REFERENCE_IMAGE_PATH = (
    Path(__file__).parent / "assets" / "model_regression" / "traffic_reference.jpg"
)


@pytest.fixture(scope="module")
def reference_image():
    assert REFERENCE_IMAGE_PATH.exists(), (
        f"Reference image missing at: {REFERENCE_IMAGE_PATH}. "
        "The model regression test requires an immutable local asset."
    )
    img = cv2.imread(str(REFERENCE_IMAGE_PATH))
    assert img is not None, f"Failed to decode reference image from {REFERENCE_IMAGE_PATH}"
    assert img.ndim == 3 and img.shape[2] == 3, "Image must be a 3-channel color image"
    return img


@pytest.fixture(scope="module")
def detector():
    return VehicleDetector()


def test_reference_image_structural_invariants(detector, reference_image):
    """
    Assert that running inference on the reference image yields expected
    structural invariants: non-empty detections, valid classes, valid bounds,
    and reasonable CPU latency.
    """
    h, w, _ = reference_image.shape
    detections, latency_ms = detector.detect(reference_image)

    # 1. At least 1 vehicle detected and not an absurdly large number
    assert 1 <= len(detections) <= 20, (
        f"Unexpected detection count {len(detections)} on reference image"
    )

    # 2. Latency is recorded, non-negative, and within acceptable CPU threshold (< 1000ms)
    assert 0.0 < latency_ms < 1000.0, f"Inference latency {latency_ms}ms outside bounds"

    # 3. Structural checks on each bounding box and class
    for det in detections:
        assert det.class_name in TARGET_CLASS_NAMES, (
            f"Detected class '{det.class_name}' is not in TARGET_CLASS_NAMES"
        )
        assert 0.0 <= det.confidence <= 1.0, (
            f"Confidence {det.confidence} not in [0.0, 1.0]"
        )

        x1, y1, x2, y2 = det.bbox
        assert 0 <= x1 < x2 <= w, f"Bbox x-coords ({x1}, {x2}) invalid for width {w}"
        assert 0 <= y1 < y2 <= h, f"Bbox y-coords ({y1}, {y2}) invalid for height {h}"

    # 4. Primary detection check: reference image contains a prominent bus with high confidence
    bus_dets = [d for d in detections if d.class_name == "bus"]
    assert len(bus_dets) >= 1, "Expected at least 1 'bus' detection in reference image"
    max_bus_conf = max(d.confidence for d in bus_dets)
    assert max_bus_conf >= 0.70, (
        f"Expected prominent bus confidence >= 0.70, got {max_bus_conf:.3f}"
    )


def test_inference_stability_and_repeatability(detector, reference_image):
    """
    Assert that repeated inference on the same static image produces stable
    detection counts, consistent classes, and bounding boxes within tight tolerances
    (not requiring bit-exact float equality across BLAS/hardware backends).
    """
    runs = []
    for _ in range(3):
        dets, _ = detector.detect(reference_image)
        runs.append(dets)

    # All runs must produce identical detection count
    counts = [len(r) for r in runs]
    assert all(c == counts[0] for c in counts), f"Inconsistent detection counts across runs: {counts}"

    base_run = runs[0]
    for run_idx, run in enumerate(runs[1:], start=2):
        for det_base, det_other in zip(base_run, run):
            # Class match
            assert det_base.class_name == det_other.class_name, (
                f"Class mismatch between run 1 ({det_base.class_name}) and run {run_idx} ({det_other.class_name})"
            )

            # Confidence tolerance (within 0.05)
            assert abs(det_base.confidence - det_other.confidence) <= 0.05, (
                f"Confidence drift > 0.05: {det_base.confidence} vs {det_other.confidence}"
            )

            # Coordinate tolerance: bounding box within 3 pixels
            box_diff = np.abs(np.array(det_base.bbox) - np.array(det_other.bbox))
            assert np.all(box_diff <= 3.0), (
                f"Bbox coordinate drift > 3px: {det_base.bbox} vs {det_other.bbox} (diff={box_diff})"
            )
