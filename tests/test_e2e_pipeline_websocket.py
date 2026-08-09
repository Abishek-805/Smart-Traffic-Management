"""
End-to-End Integration Test for Smart Traffic Management System.
Verifies: REGISTER_CAMERA → VIDEO_FRAME → TrafficPipeline → PipelineResult → ControlManager → PipelineStateSnapshot.
"""

import unittest
import base64
import cv2
import numpy as np
import asyncio

from web.app import app
from core.application_context import ApplicationContext
from server.message_handler import MessageHandler


class TestE2EPipelineWebSocket(unittest.IsolatedAsyncioTestCase):
    """End-to-end integration test verifying full mobile camera frame ingestion through TrafficPipeline."""

    async def test_e2e_camera_to_traffic_pipeline_flow(self):
        """Verify that incoming camera frames trigger TrafficPipeline, update ControlManager, and generate a valid snapshot."""
        handler = MessageHandler()
        ctx = ApplicationContext.get_instance()

        # 1. Register Camera Node
        reg_packet = {
            "protocol_version": "1.0",
            "message_type": "REGISTER_CAMERA",
            "id": "req-001",
            "payload": {
                "node_id": "TEST-CAM-NORTH",
                "camera_direction": "north",
            },
        }

        class MockWebSocket:
            async def accept(self): pass
            async def send_json(self, data): pass

        mock_ws = MockWebSocket()
        reg_response = await handler.process_message(reg_packet, mock_ws)
        self.assertIsNotNone(reg_response)
        self.assertEqual(reg_response.get("message_type"), "REGISTRATION_ACK")

        # 2. Generate synthetic black frame with white rectangle (vehicle mock)
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.rectangle(img, (100, 100), (300, 300), (255, 255, 255), -1)
        ret, enc = cv2.imencode(".jpg", img)
        self.assertTrue(ret)
        frame_b64 = base64.b64encode(enc.tobytes()).decode("utf-8")

        frame_packet = {
            "protocol_version": "1.0",
            "message_type": "VIDEO_FRAME",
            "payload": {
                "node_id": "TEST-CAM-NORTH",
                "direction": "north",
                "frame_data": frame_b64,
            },
        }

        # 3. Transmit VIDEO_FRAME message to MessageHandler
        await handler.process_message(frame_packet, mock_ws)

        # Allow worker thread execution to complete (wait up to 40s for model load)
        for _ in range(400):
            if ctx.latest_snapshot is not None:
                break
            await asyncio.sleep(0.1)

        # 4. Verify ApplicationContext snapshot and pipeline state
        snapshot = ctx.latest_snapshot
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.get("type"), "SystemStatusUpdated")
        self.assertIn("payload", snapshot)
        self.assertIn("activePhase", snapshot["payload"])
        self.assertIn("totalVehicles", snapshot["payload"])

        # Verify frame buffer contains annotated JPEG bytes
        self.assertIn("north", ctx.frame_buffer)
        self.assertIsInstance(ctx.frame_buffer["north"], bytes)


if __name__ == "__main__":
    unittest.main()

