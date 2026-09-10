"""Unit and integration tests for LocalCameraSources."""
import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

from server.connection_manager import ConnectionManager
from server.session_manager import SessionManager
from server.local_sources import LocalCameraSources


class TestLocalCameraSources(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.handler = MagicMock()
        self.handler.session_manager = SessionManager(timeout_sec=120)
        self.handler.connection_manager = ConnectionManager()
        self.handler.submit_decoded_frame = AsyncMock()

    async def asyncTearDown(self):
        if "TRAFFIC_SOURCES_JSON" in os.environ:
            del os.environ["TRAFFIC_SOURCES_JSON"]

    async def test_invalid_sources_json_rejected(self):
        # Non-dict JSON
        os.environ["TRAFFIC_SOURCES_JSON"] = "[\"north\"]"
        sources = LocalCameraSources(self.handler)
        with self.assertRaises(ValueError):
            await sources.start()

        # Invalid direction key
        os.environ["TRAFFIC_SOURCES_JSON"] = '{"invalid_direction": 0}'
        sources = LocalCameraSources(self.handler)
        with self.assertRaises(ValueError):
            await sources.start()

    async def test_invalid_source_type_rejected(self):
        # Boolean is rejected
        os.environ["TRAFFIC_SOURCES_JSON"] = '{"north": true}'
        sources = LocalCameraSources(self.handler)
        with self.assertRaises(ValueError):
            await sources.start()

        # List/dict is rejected
        os.environ["TRAFFIC_SOURCES_JSON"] = '{"north": [1, 2]}'
        sources = LocalCameraSources(self.handler)
        with self.assertRaises(ValueError):
            await sources.start()

    async def test_occupied_direction_rejected(self):
        self.handler.session_manager.create_session("EXISTING-NORTH", "north")
        os.environ["TRAFFIC_SOURCES_JSON"] = '{"north": 0}'
        sources = LocalCameraSources(self.handler)
        with self.assertRaises(ValueError):
            await sources.start()

    async def test_local_capture_frame_submission_and_shutdown(self):
        os.environ["TRAFFIC_SOURCES_JSON"] = '{"north": 0}'
        sources = LocalCameraSources(self.handler)

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        test_img = np.zeros((120, 160, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, test_img)

        with patch("cv2.VideoCapture", return_value=mock_cap):
            await sources.start()

            # Session and active connection created
            self.assertIn("LOCAL-north", self.handler.connection_manager.active_connections)
            session = self.handler.session_manager.get_session("LOCAL-north")
            self.assertIsNotNone(session)
            self.assertTrue(session.streaming)

            # Wait for pump loop to deliver at least one frame
            for _ in range(20):
                if self.handler.submit_decoded_frame.call_count >= 1:
                    break
                await asyncio.sleep(0.05)

            self.assertGreaterEqual(self.handler.submit_decoded_frame.call_count, 1)
            call_args = self.handler.submit_decoded_frame.call_args[0]
            # (image, direction, node, token, connection, frame_id, received)
            np.testing.assert_array_equal(call_args[0], test_img)
            self.assertEqual(call_args[1], "north")
            self.assertEqual(call_args[2], "LOCAL-north")

            await sources.shutdown()

            # Sessions and connections cleaned up
            self.assertNotIn("LOCAL-north", self.handler.connection_manager.active_connections)
            self.assertIsNone(self.handler.session_manager.get_session("LOCAL-north"))


if __name__ == "__main__":
    unittest.main()
