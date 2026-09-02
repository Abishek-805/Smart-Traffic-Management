"""
Unit and integration tests for Phase 2 Sprint 1 Communication Server (FastAPI / WebSockets / Protocol / Sessions).
"""

import unittest
import time
import asyncio
from fastapi.testclient import TestClient

from server import (
    app,
    MessageType,
    PROTOCOL_VERSION,
    RegistrationMessage,
    CameraRegistrationPayload,
    HeartbeatMessage,
    HeartbeatPayload,
    DisconnectMessage,
    DisconnectPayload,
    SessionManager,
    ConnectionManager,
    MessageHandler,
)
from server.websocket_server import message_handler as app_message_handler


class TestCommunicationServer(unittest.TestCase):
    """Test suite for server package protocol, session management, and WebSocket endpoint."""

    def setUp(self):
        self.session_mgr = SessionManager(timeout_sec=5.0)
        self.conn_mgr = ConnectionManager()
        self.handler = MessageHandler(session_manager=self.session_mgr, connection_manager=self.conn_mgr)
        self.client = TestClient(app)

    def test_01_protocol_pydantic_schemas(self):
        """Test Pydantic schema validation and MessageType Enum."""
        msg = RegistrationMessage(
            payload=CameraRegistrationPayload(
                node_id="CAM-NORTH-01",
                camera_direction="north",
                resolution="1920x1080",
                fps=30.0,
            )
        )
        d = msg.model_dump()
        self.assertEqual(d["message_type"], MessageType.REGISTER_CAMERA.value)
        self.assertEqual(d["protocol_version"], PROTOCOL_VERSION)
        self.assertEqual(d["payload"]["node_id"], "CAM-NORTH-01")

    def test_02_session_manager_crud_and_expiration(self):
        """Test SessionManager create, validate, heartbeat update, and expiration."""
        session = self.session_mgr.create_session("CAM-SOUTH-01", "south")
        self.assertIsNotNone(session.session_token)
        self.assertTrue(self.session_mgr.validate_session("CAM-SOUTH-01", session.session_token))
        self.assertFalse(self.session_mgr.validate_session("CAM-SOUTH-01", "INVALID_TOKEN"))

        # Update heartbeat
        success = self.session_mgr.update_heartbeat("CAM-SOUTH-01", session.session_token)
        self.assertTrue(success)

        # Remove session
        removed = self.session_mgr.remove_session("CAM-SOUTH-01")
        self.assertIsNotNone(removed)
        self.assertFalse(self.session_mgr.validate_session("CAM-SOUTH-01", session.session_token))

    def test_03_reconnect_duplicate_node_id(self):
        """Test duplicate node_id reconnection replaces old session gracefully."""
        sess1 = self.session_mgr.create_session("CAM-EAST-01", "east")
        sess2 = self.session_mgr.create_session("CAM-EAST-01", "east")

        self.assertNotEqual(sess1.session_token, sess2.session_token)
        self.assertFalse(self.session_mgr.validate_session("CAM-EAST-01", sess1.session_token))
        self.assertTrue(self.session_mgr.validate_session("CAM-EAST-01", sess2.session_token))

    def test_04_message_handler_registration_and_heartbeat(self):
        """Test MessageHandler processing REGISTER_CAMERA and HEARTBEAT packets."""
        self.session_mgr.register_pairing_session("west", "CAM-WEST-01", "west-pair", time.time() + 60)
        reg_pkt = {
            "message_type": "REGISTER_CAMERA",
            "protocol_version": PROTOCOL_VERSION,
            "timestamp": time.time(),
            "token": "west-pair",
            "payload": {
                "node_id": "CAM-WEST-01",
                "camera_direction": "west",
            },
        }

        def _get_val(m):
            return m.value if hasattr(m, "value") else str(m)

        # Run async message processing
        res = asyncio.run(self.handler.process_message(reg_pkt, websocket=None))
        self.assertIsNotNone(res)
        self.assertEqual(_get_val(res["message_type"]), "REGISTRATION_ACK")
        self.assertEqual(res["payload"]["node_id"], "CAM-WEST-01")
        token = res["payload"]["session_token"]
        self.assertTrue(token)

        # Heartbeat packet
        hb_pkt = {
            "message_type": "HEARTBEAT",
            "protocol_version": PROTOCOL_VERSION,
            "timestamp": time.time(),
            "payload": {
                "node_id": "CAM-WEST-01",
                "session_token": token,
            },
        }
        res_hb = asyncio.run(self.handler.process_message(hb_pkt, websocket=None))
        self.assertEqual(_get_val(res_hb["message_type"]), "HEARTBEAT_ACK")
        self.assertEqual(res_hb["payload"]["status"], "OK")

    def test_05_message_handler_errors(self):
        """Test MessageHandler error handling for malformed packets and invalid tokens."""
        def _get_val(m):
            return m.value if hasattr(m, "value") else str(m)

        # Malformed packet
        res_err = asyncio.run(self.handler.process_message({"bad": "data"}, websocket=None))
        self.assertEqual(_get_val(res_err["message_type"]), "ERROR")
        self.assertEqual(res_err["payload"]["error_code"], "MISSING_MESSAGE_TYPE")

        # Invalid protocol version
        res_ver = asyncio.run(
            self.handler.process_message(
                {"message_type": "REGISTER_CAMERA", "protocol_version": "9.9"}, websocket=None
            )
        )
        self.assertEqual(_get_val(res_ver["message_type"]), "ERROR")
        self.assertEqual(res_ver["payload"]["error_code"], "PROTOCOL_VERSION_MISMATCH")

        # Invalid heartbeat token
        hb_err = asyncio.run(
            self.handler.process_message(
                {
                    "message_type": "HEARTBEAT",
                    "protocol_version": PROTOCOL_VERSION,
                    "payload": {"node_id": "CAM-WEST-01", "session_token": "FAKE_TOKEN"},
                },
                websocket=None,
            )
        )
        self.assertEqual(_get_val(hb_err["message_type"]), "ERROR")
        self.assertEqual(hb_err["payload"]["error_code"], "UNAUTHORIZED_SESSION")

    def test_06_fastapi_websocket_endpoint_flow(self):
        """Test FastAPI TestClient WebSocket connection to /ws/camera endpoint."""
        pairing = {"session": "CAM-TEST-101", "token": "test-pair"}
        app_message_handler.session_manager.register_pairing_session(
            "north", pairing["session"], pairing["token"], time.time() + 60
        )
        with self.client.websocket_connect("/ws/camera") as websocket:
            # 1. Send REGISTER_CAMERA
            websocket.send_json(
                {
                    "message_type": "REGISTER_CAMERA",
                    "protocol_version": PROTOCOL_VERSION,
                    "timestamp": time.time(),
                    "token": pairing["token"],
                    "payload": {
                        "node_id": pairing["session"],
                        "camera_direction": "north",
                        "resolution": "1280x720",
                        "fps": 30.0,
                    },
                }
            )

            ack_data = websocket.receive_json()
            self.assertEqual(ack_data["message_type"], "REGISTRATION_ACK")
            self.assertEqual(ack_data["payload"]["node_id"], pairing["session"])
            token = ack_data["payload"]["session_token"]
            self.assertTrue(token)

            # 1b. Receive automatic START_STREAM packet
            start_pkt = websocket.receive_json()
            self.assertIn(start_pkt.get("message_type"), ["START_STREAM", "REGISTRATION_ACK"])

            # 2. Send HEARTBEAT
            websocket.send_json(
                {
                    "message_type": "HEARTBEAT",
                    "protocol_version": PROTOCOL_VERSION,
                    "timestamp": time.time(),
                    "payload": {
                        "node_id": pairing["session"],
                        "session_token": token,
                        "uptime_sec": 12.5,
                    },
                }
            )

            hb_ack = websocket.receive_json()
            self.assertEqual(hb_ack["message_type"], "HEARTBEAT_ACK")
            self.assertEqual(hb_ack["payload"]["status"], "OK")

            # 3. Send DISCONNECT
            websocket.send_json(
                {
                    "message_type": "DISCONNECT",
                    "protocol_version": PROTOCOL_VERSION,
                    "timestamp": time.time(),
                    "payload": {
                        "node_id": pairing["session"],
                        "session_token": token,
                        "reason": "Test finished",
                    },
                }
            )

    def test_07_four_independent_phone_sessions(self):
        """Four phones can pair concurrently; identity is not tied to client IP."""
        async def scenario():
            directions = ("north", "east", "south", "west")

            class MockWebSocket:
                async def send_json(self, data): pass
                async def close(self, code=1000, reason=None): pass

            sockets = {direction: MockWebSocket() for direction in directions}
            packets = []
            for direction in directions:
                node = f"PHONE-{direction.upper()}"
                token = f"pair-{direction}"
                self.session_mgr.register_pairing_session(
                    direction, node, token, time.time() + 60
                )
                packets.append((direction, node, {
                    "message_type": "REGISTER_CAMERA",
                    "protocol_version": PROTOCOL_VERSION,
                    "token": token,
                    "payload": {"node_id": node, "camera_direction": direction},
                }))

            responses = await asyncio.gather(*(
                self.handler.process_message(packet, sockets[direction])
                for direction, _, packet in packets
            ))
            self.assertTrue(all(response["type"] == "REGISTRATION_ACK" for response in responses))
            self.assertEqual(len(self.session_mgr.sessions), 4)
            self.assertEqual(len(self.conn_mgr.active_connections), 4)
            self.assertEqual(
                {session.camera_direction for session in self.session_mgr.sessions.values()},
                set(directions),
            )

            # A north phone cannot submit a frame or heartbeat as east even if
            # both phones share an address behind the same Wi-Fi router.
            north_response = responses[0]
            mismatch = await self.handler.process_message({
                "message_type": "HEARTBEAT",
                "protocol_version": PROTOCOL_VERSION,
                "payload": {
                    "node_id": "PHONE-NORTH",
                    "session_token": north_response["payload"]["session_token"],
                    "direction": "east",
                },
            }, sockets["north"])
            self.assertEqual(mismatch["payload"]["error_code"], "DIRECTION_MISMATCH")

        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
