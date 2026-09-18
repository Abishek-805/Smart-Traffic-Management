"""
Automated negative and boundary test suite for REST APIs and WebSocket endpoints.
Verifies HTTP 422/404/503 status codes, input boundaries, malformed packets, and security rejections.
"""

import time
import pytest
from fastapi.testclient import TestClient
from web.app import app
from server.websocket_server import message_handler


@pytest.fixture
def client():
    return TestClient(app)


def test_qr_generate_invalid_direction(client):
    res = client.get("/api/v1/qr/generate?direction=northwest")
    assert res.status_code == 422
    assert "Choose north, south, east or west" in res.json().get("detail", "")


def test_camera_feed_invalid_direction(client):
    res = client.get("/api/v1/cameras/invalid_dir/feed")
    assert res.status_code == 422
    assert "Choose north, south, east or west" in res.json().get("detail", "")


def test_camera_delete_invalid_direction(client):
    res = client.delete("/api/v1/cameras/skyward")
    assert res.status_code == 422
    assert "Choose north, south, east or west" in res.json().get("detail", "")


def test_camera_post_rejects_manual_config(client):
    res = client.post("/api/v1/cameras/north", json={"ip": "192.168.1.50"})
    assert res.status_code == 422
    assert "This runtime accepts mobile cameras" in res.json().get("detail", "")


def test_system_config_bounds(client):
    # Confidence out of bounds (< 0.05)
    res_low_conf = client.post("/api/v1/system/config", json={
        "confidenceThreshold": 0.01,
        "minGreenTime": 10,
        "maxGreenTime": 30
    })
    assert res_low_conf.status_code == 422

    # Confidence out of bounds (> 0.95)
    res_high_conf = client.post("/api/v1/system/config", json={
        "confidenceThreshold": 0.99,
        "minGreenTime": 10,
        "maxGreenTime": 30
    })
    assert res_high_conf.status_code == 422

    # Min green < 5
    res_low_green = client.post("/api/v1/system/config", json={
        "confidenceThreshold": 0.5,
        "minGreenTime": 2,
        "maxGreenTime": 30
    })
    assert res_low_green.status_code == 422

    # Min green > Max green
    res_inverted_green = client.post("/api/v1/system/config", json={
        "confidenceThreshold": 0.5,
        "minGreenTime": 45,
        "maxGreenTime": 30
    })
    assert res_inverted_green.status_code == 422

    # Max green > 120
    res_excessive_green = client.post("/api/v1/system/config", json={
        "confidenceThreshold": 0.5,
        "minGreenTime": 10,
        "maxGreenTime": 150
    })
    assert res_excessive_green.status_code == 422

    # Malformed / missing fields
    res_missing = client.post("/api/v1/system/config", json={
        "confidenceThreshold": "not_a_number"
    })
    assert res_missing.status_code == 422


def test_logs_query_limit_bounds(client):
    # Limit < 1
    res_zero = client.get("/api/v1/logs?limit=0")
    assert res_zero.status_code == 422

    # Limit > 1000
    res_huge = client.get("/api/v1/logs?limit=2000")
    assert res_huge.status_code == 422

    # Valid limit
    res_valid = client.get("/api/v1/logs?limit=50")
    assert res_valid.status_code == 200
    assert res_valid.json()["success"] is True


def test_legacy_api_loop_prevention(client):
    # Direct /api/v1 should not redirect into /api/v1/v1
    res = client.get("/api/v1")
    assert res.status_code == 404

    res_sub = client.get("/api/v1/nonexistent_route")
    assert res_sub.status_code == 404


def test_websocket_missing_message_type(client):
    with client.websocket_connect("/ws/camera") as ws:
        ws.send_json({"payload": {}})
        err = ws.receive_json()
        assert err["payload"]["error_code"] == "MISSING_MESSAGE_TYPE"


def test_websocket_protocol_version_mismatch(client):
    with client.websocket_connect("/ws/camera") as ws:
        ws.send_json({
            "message_type": "REGISTER_CAMERA",
            "protocol_version": "99.0",
            "payload": {}
        })
        err = ws.receive_json()
        assert err["payload"]["error_code"] == "PROTOCOL_VERSION_MISMATCH"


def test_websocket_unknown_message_type(client):
    with client.websocket_connect("/ws/camera") as ws:
        ws.send_json({
            "message_type": "EXPLODE_NOW",
            "protocol_version": "1.0",
            "payload": {}
        })
        err = ws.receive_json()
        assert err["payload"]["error_code"] == "UNKNOWN_MESSAGE_TYPE"


def test_websocket_unauthorized_frame(client):
    with client.websocket_connect("/ws/camera") as ws:
        ws.send_json({
            "message_type": "VIDEO_FRAME",
            "protocol_version": "1.0",
            "payload": {
                "node_id": "UNREGISTERED_NODE",
                "session_token": "FAKE_TOKEN",
                "direction": "north"
            }
        })
        err = ws.receive_json()
        assert err["payload"]["error_code"] == "UNAUTHORIZED_SESSION"


def test_websocket_register_invalid_direction(client):
    with client.websocket_connect("/ws/camera") as ws:
        ws.send_json({
            "message_type": "REGISTER_CAMERA",
            "protocol_version": "1.0",
            "token": "some-token",
            "payload": {
                "node_id": "CAM-TEST-01",
                "camera_direction": "northwest"
            }
        })
        err = ws.receive_json()
        assert err["payload"]["error_code"] == "INVALID_DIRECTION"


def test_websocket_register_unauthorized_pairing(client):
    with client.websocket_connect("/ws/camera") as ws:
        ws.send_json({
            "message_type": "REGISTER_CAMERA",
            "protocol_version": "1.0",
            "token": "unregistered-secret",
            "payload": {
                "node_id": "CAM-TEST-02",
                "camera_direction": "north"
            }
        })
        err = ws.receive_json()
        assert err["payload"]["error_code"] == "UNAUTHORIZED_PAIRING"


def test_operator_auth_enforcement(client, monkeypatch):
    # When OPERATOR_API_KEY is configured, unauthenticated requests are rejected with 401
    monkeypatch.setenv("OPERATOR_API_KEY", "prod-secure-token-1234")

    # Missing header
    res_missing = client.post("/api/v1/system/start")
    assert res_missing.status_code == 401
    assert "Unauthorized" in res_missing.json().get("detail", "")

    # Wrong header
    res_wrong = client.post("/api/v1/system/start", headers={"X-Operator-Token": "wrong-key"})
    assert res_wrong.status_code == 401

    # Correct header -> passes authentication (proceeds to handler or service)
    res_correct = client.post("/api/v1/system/start", headers={"X-Operator-Token": "prod-secure-token-1234"})
    assert res_correct.status_code != 401
