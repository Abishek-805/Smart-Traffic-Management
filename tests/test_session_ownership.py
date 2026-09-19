import pytest

from server.connection_manager import ConnectionManager
from server.session_manager import SessionManager


class FakeWebSocket:
    def __init__(self):
        self.closed = False
        self.close_code = None
        self.close_reason = None

    async def close(self, code=1000, reason=None):
        self.closed = True
        self.close_code = code
        self.close_reason = reason


def test_old_generation_cannot_remove_reconnected_session():
    sessions = SessionManager(timeout_sec=10)
    old = sessions.create_session("cam-n", "north")

    new = sessions.replace_session(
        "cam-n", "north", reconnect_token=old.session_token
    )

    assert new.generation != old.generation
    assert new.session_token == old.session_token
    assert sessions.remove_session("cam-n", generation=old.generation) is None
    assert sessions.get_session("cam-n") is new


@pytest.mark.asyncio
async def test_old_socket_disconnect_cannot_remove_new_connection():
    manager = ConnectionManager()
    old_ws = FakeWebSocket()
    new_ws = FakeWebSocket()
    await manager.connect("cam-n", old_ws, generation="g1")
    await manager.connect("cam-n", new_ws, generation="g2")

    removed = await manager.disconnect(
        "cam-n", generation="g1", websocket=old_ws
    )

    assert removed is False
    assert manager.get_connection("cam-n") is new_ws
    assert old_ws.closed is True
    assert new_ws.closed is False
