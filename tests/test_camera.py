"""
Unit tests for CameraStream, CameraManager, StreamConfig, and MultiCameraDashboard.
"""

import unittest
import tempfile
from pathlib import Path
import numpy as np
import cv2

from ai.camera import (
    CameraStream,
    CameraManager,
    STREAM_CONFIG,
    validate_stream_sources,
)
from dashboard.multi_camera_dashboard import MultiCameraDashboard
from config.paths import VIDEOS_DIR


class TestCameraPackage(unittest.TestCase):
    """Test suite for Camera infrastructure package and multi-camera dashboard."""

    def test_01_stream_config_and_validation(self):
        """Test STREAM_CONFIG layout and file validation logic."""
        self.assertEqual(STREAM_CONFIG, {})
        validate_stream_sources(STREAM_CONFIG)

        # Invalid file raises FileNotFoundError
        invalid_config = {"invalid_cam": VIDEOS_DIR / "non_existent_video.mp4"}
        with self.assertRaises(FileNotFoundError):
            validate_stream_sources(invalid_config)

    def test_02_camera_stream_operations(self):
        """Test single CameraStream creation, frame reading, and resource release."""
        fixture = cv2.imread(str(Path(__file__).parent / "fixtures" / "ultralytics_bus.jpg"))
        self.assertIsNotNone(fixture)
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "real_fixture.avi"
            writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"MJPG"), 2, (fixture.shape[1], fixture.shape[0]))
            writer.write(fixture)
            writer.release()
            stream = CameraStream(source=video, lane_name="north")

            self.assertTrue(stream.is_connected())
            self.assertEqual(stream.lane_name, "north")

            success, frame, meta = stream.read()
            self.assertTrue(success)
            self.assertIsNotNone(frame)
            self.assertIsInstance(frame, np.ndarray)

        # Verify metadata structure
            self.assertEqual(meta["lane_name"], "north")
            self.assertTrue(meta["connected"])
            self.assertGreater(meta["fps"], 0)
            self.assertEqual(meta["frame_number"], 1)

            stream.release()
            self.assertFalse(stream.is_connected())

    def test_03_camera_manager_operations(self):
        """Test CameraManager collection initialization, multi-stream reading, and health status."""
        manager = CameraManager(config={})
        self.assertEqual(manager.streams, {})
        self.assertEqual(manager.read_all(), {})
        self.assertEqual(manager.get_health(), {})
        self.assertEqual(manager.get_status(), {})
        self.assertEqual(manager.get_frames(), {})

        manager.stop_all()

    def test_04_multi_camera_dashboard_rendering(self):
        """Test MultiCameraDashboard grid composition with active and disconnected streams."""
        dashboard = MultiCameraDashboard(tile_width=320, tile_height=180)

        mock_frame = np.zeros((180, 320, 3), dtype=np.uint8)
        mock_data = {
            "north": {"frame": mock_frame, "connected": True, "fps": 30.0, "resolution": (320, 180), "frame_number": 10},
            "south": {"frame": mock_frame, "connected": True, "fps": 30.0, "resolution": (320, 180), "frame_number": 10},
            "east": {"frame": mock_frame, "connected": True, "fps": 30.0, "resolution": (320, 180), "frame_number": 10},
            "west": {"frame": None, "connected": False, "fps": 0.0, "resolution": (0, 0), "frame_number": 0},
        }

        composite = dashboard.render(mock_data)
        self.assertIsNotNone(composite)
        self.assertIsInstance(composite, np.ndarray)
        self.assertGreater(composite.shape[0], 0)
        self.assertGreater(composite.shape[1], 0)


if __name__ == "__main__":
    unittest.main()
