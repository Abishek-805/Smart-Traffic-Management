"""
Unit tests for Production Web Control Center (Service Layer, ApplicationContext, MJPEG Feeds, REST APIs, WebSockets).
"""

import unittest
from fastapi.testclient import TestClient
from web.app import app


class TestWebApplication(unittest.TestCase):
    """Test suite for Web Control Center HTML pages, REST APIs, and WebSockets."""

    def setUp(self):
        self.client = TestClient(app)

    def test_01_html_routes_render(self):
        """Verify main web routes return status 200."""
        routes = ["/"]
        for path in routes:
            res = self.client.get(path)
            self.assertEqual(res.status_code, 200, f"Path '{path}' failed with status {res.status_code}")

    def test_02_api_system_health(self):
        """Verify GET /api/v1/system/health returns structured diagnostic metrics."""
        res = self.client.get("/api/v1/system/health")
        self.assertEqual(res.status_code, 200)
        envelope = res.json()
        self.assertTrue(envelope.get("success"))
        data = envelope.get("data", {})
        self.assertIn("system_status", data)
        self.assertIn("components", data)

    def test_03_api_system_status_and_actions(self):
        """Verify REST API start/stop/restart control actions."""
        res_status = self.client.get("/api/v1/system/status")
        self.assertEqual(res_status.status_code, 200)

        res_start = self.client.post("/api/v1/system/start")
        self.assertEqual(res_start.status_code, 200)

        res_stop = self.client.post("/api/v1/system/stop")
        self.assertEqual(res_stop.status_code, 200)

    def test_04_api_qr_generation(self):
        """Verify GET /api/v1/qr/generate returns payload JSON and base64 QR image string."""
        res = self.client.get("/api/v1/qr/generate")
        self.assertEqual(res.status_code, 200)
        envelope = res.json()
        data = envelope.get("data", {})
        self.assertIn("payload", data)
        self.assertIn("qr_image", data)
        self.assertTrue(data["qr_image"].startswith("data:image/"))

    def test_05_camera_mjpeg_feed_endpoint(self):
        """Verify GET /api/v1/cameras/north/feed returns streaming response."""
        with self.client.stream("GET", "/api/v1/cameras/north/feed") as res:
            self.assertEqual(res.status_code, 200)
            self.assertTrue(res.headers["content-type"].startswith("multipart/x-mixed-replace"))
            res.close()

    def test_06_camera_node_websocket_integration(self):
        """Verify /ws/camera endpoint functions on single unified FastAPI app."""
        with self.client.websocket_connect("/ws/camera") as ws:
            ws.send_json({
                "type": "REGISTER_CAMERA",
                "payload": {"node_id": "CAM-WEB-01", "camera_direction": "north"}
            })
            ack = ws.receive_json()
            self.assertEqual(ack.get("type"), "REGISTRATION_ACK")


if __name__ == "__main__":
    unittest.main()

