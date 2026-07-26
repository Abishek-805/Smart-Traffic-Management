"""
Integration unit tests for Sprint 5 Multi-Camera TrafficPipeline AI integration.
"""

import unittest
from pathlib import Path
import numpy as np

from ai.camera import CameraManager, STREAM_CONFIG
from ai.pipeline.traffic_pipeline import TrafficPipeline
from ai.pipeline.pipeline_result import PipelineResult
from ai.pipeline.intersection_state import IntersectionState, LaneProcessingResult
from dashboard.multi_camera_dashboard import MultiCameraDashboard


class TestMultiCameraPipeline(unittest.TestCase):
    """Test suite for Sprint 5 Multi-Camera Traffic Pipeline and IntersectionState."""

    @classmethod
    def setUpClass(cls):
        """Initialize multi-camera manager and pipeline."""
        cls.camera_manager = CameraManager(config=STREAM_CONFIG)
        cls.pipeline = TrafficPipeline(
            camera_manager=cls.camera_manager,
            save_output=False,
        )
        cls.dashboard = MultiCameraDashboard()

    @classmethod
    def tearDownClass(cls):
        """Clean up pipeline resources."""
        cls.pipeline.release()

    def test_01_pipeline_initialization(self):
        """Verify pipeline per-lane components and trackers are initialized."""
        self.assertEqual(len(self.pipeline.trackers), 4)
        self.assertEqual(len(self.pipeline.lane_managers), 4)
        self.assertEqual(len(self.pipeline.state_managers), 4)
        self.assertEqual(len(self.pipeline.analytics_exporters), 4)

        for lane in ["north", "south", "east", "west"]:
            self.assertIn(lane, self.pipeline.trackers)
            self.assertIn(lane, self.pipeline.lane_managers)

    def test_02_process_multi_camera_step(self):
        """Verify multi-camera frame step processing, LaneProcessingResult, and IntersectionState."""
        res: PipelineResult = self.pipeline.process_step()

        self.assertTrue(res.has_frame)
        self.assertIsNotNone(res.annotated_frame)
        self.assertIsInstance(res.annotated_frame, np.ndarray)

        # Verify LaneProcessingResult per camera
        self.assertIsInstance(res.lane_results, dict)
        self.assertEqual(len(res.lane_results), 4)
        for lane_name, lane_res in res.lane_results.items():
            self.assertIsInstance(lane_res, LaneProcessingResult)
            self.assertTrue(lane_res.connected)
            self.assertIsNotNone(lane_res.statistics)

        # Verify IntersectionState dataclass
        self.assertIsNotNone(res.intersection_state)
        self.assertIsInstance(res.intersection_state, IntersectionState)
        self.assertEqual(len(res.intersection_state.lanes), 4)
        self.assertGreaterEqual(res.intersection_state.total_vehicles, 0)

        for lane in ["north", "south", "east", "west"]:
            self.assertIn(lane, res.intersection_state.lanes)
            stats = res.intersection_state.lanes[lane]
            self.assertIsNotNone(stats)

    def test_03_signal_decision_engine_integration(self):
        """Verify Signal Decision Engine receives multi-camera IntersectionState and makes decisions."""
        res: PipelineResult = self.pipeline.process_step()

        self.assertIsNotNone(res.signal_decision)
        self.assertIn(res.signal_decision.green_lane.lower(), ["north", "south", "east", "west"])
        self.assertGreater(res.signal_decision.green_duration_sec, 0)

        self.assertIsNotNone(res.hardware_command)
        json_str = res.hardware_command.to_json()
        self.assertIn("SIGNAL_PHASE", json_str)
        self.assertIsNotNone(res.hardware_command.green_lane)

    def test_04_decoupled_dashboard_rendering(self):
        """Verify MultiCameraDashboard renders downstream directly from PipelineResult object."""
        res: PipelineResult = self.pipeline.process_step()
        canvas = self.dashboard.render_from_result(res)

        self.assertIsNotNone(canvas)
        self.assertIsInstance(canvas, np.ndarray)
        self.assertGreater(canvas.shape[0], 0)
        self.assertGreater(canvas.shape[1], 0)


if __name__ == "__main__":
    unittest.main()
