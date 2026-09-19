import time

import pytest

from server.camera_lifecycle import CameraLifecycleState, CameraStatusSnapshot
from server.connection_manager import ConnectionManager
from server.message_handler import MessageHandler
from server.session_manager import SessionManager
from core.application_context import ApplicationContext
from server.runtime import runtime_snapshot


class FakeClock:
    def __init__(self, now=100.0):
        self.value = now

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class FakeWebSocket:
    def __init__(self):
        self.closed = False

    async def close(self, code=1000, reason=None):
        self.closed = True

    async def send_json(self, data):
        return None


def registration(node_id, direction, token):
    return {
        "type": "REGISTER_CAMERA",
        "message_type": "REGISTER_CAMERA",
        "protocol_version": "1.0",
        "token": token,
        "payload": {
            "node_id": node_id,
            "camera_direction": direction,
        },
    }


def test_authenticated_socket_without_media_is_connecting():
    status = CameraStatusSnapshot(authenticated=True, media_connected=False)

    assert status.state is CameraLifecycleState.CONNECTING


def test_runtime_node_is_not_connected_before_media_and_inference():
    ctx = ApplicationContext()
    session = ctx.session_manager.create_session("cam-n", "north")
    session.transport_alive = True

    node = runtime_snapshot(ctx)["payload"]["nodes"][0]

    assert node["status"] == "CONNECTING"


@pytest.mark.asyncio
async def test_dead_owner_is_reclaimable_after_grace():
    clock = FakeClock()
    sessions = SessionManager(timeout_sec=10)
    connections = ConnectionManager()
    handler = MessageHandler(
        session_manager=sessions,
        connection_manager=connections,
        clock=clock,
        takeover_grace_sec=1.0,
    )
    old_ws = FakeWebSocket()
    sessions.register_pairing_session("north", "old", "old-pair", time.time() + 60)
    first = await handler.process_message(
        registration("old", "north", "old-pair"), old_ws
    )
    assert first["type"] == "REGISTRATION_ACK"

    handler.handle_connection_loss("old", websocket=old_ws)
    clock.advance(handler.takeover_grace_sec + 0.01)
    sessions.register_pairing_session("north", "new", "new-pair", time.time() + 60)
    new_ws = FakeWebSocket()
    second = await handler.process_message(
        registration("new", "north", "new-pair"), new_ws
    )

    assert second["type"] == "REGISTRATION_ACK"
    assert sessions.get_session("old") is None
    assert connections.get_connection("old") is None
    assert old_ws.closed is True
    assert sessions.get_session("new").transport_alive is True
    await handler.shutdown()


@pytest.mark.asyncio
async def test_live_owner_conflict_has_retry_details():
    clock = FakeClock()
    sessions = SessionManager(timeout_sec=10)
    handler = MessageHandler(
        session_manager=sessions,
        connection_manager=ConnectionManager(),
        clock=clock,
        takeover_grace_sec=1.0,
    )
    sessions.register_pairing_session("north", "owner", "owner-pair", time.time() + 60)
    await handler.process_message(
        registration("owner", "north", "owner-pair"), FakeWebSocket()
    )
    sessions.register_pairing_session("north", "conflict", "conflict-pair", time.time() + 60)

    response = await handler.process_message(
        registration("conflict", "north", "conflict-pair"), FakeWebSocket()
    )

    assert response["payload"]["error_code"] == "DIRECTION_OCCUPIED"
    assert response["payload"]["direction"] == "north"
    assert response["payload"]["owner_state"] == "CONNECTING"
    assert response["payload"]["retry_after_ms"] > 0
    await handler.shutdown()
