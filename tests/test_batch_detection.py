import cv2
from pathlib import Path
from ai.detection.detector import VehicleDetector


def test_batch_preserves_order_and_real_detection_geometry():
    detector = VehicleDetector()
    image = cv2.imread(str(Path(__file__).parent / 'fixtures/ultralytics_bus.jpg'))
    small = cv2.resize(image, (240, 320))
    results, elapsed = detector.detect_batch([image, small], [11, 22], [1., 2.])
    assert len(results) == 2 and elapsed > 0
    for boxes, frame, number in zip(results, [image, small], [11, 22]):
        assert any(box.class_name == 'bus' for box in boxes)
        assert all(box.frame_number == number for box in boxes)
        assert all(0 <= box.bbox[0] < box.bbox[2] <= frame.shape[1] for box in boxes)
        assert all(0 <= box.bbox[1] < box.bbox[3] <= frame.shape[0] for box in boxes)
