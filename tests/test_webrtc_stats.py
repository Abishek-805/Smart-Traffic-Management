import pytest

from server.connection_manager import ConnectionManager
from server.message_handler import MessageHandler
from server.protocol import WebRTCStatsPayload
from server.session_manager import SessionManager


class Socket:
    async def close(self, **_kwargs):
        return None


def test_missing_webrtc_stats_remain_none():
    parsed = WebRTCStatsPayload.model_validate({"sent_fps": 8})

    assert parsed.sent_fps == 8
    assert parsed.packet_loss is None
    assert parsed.jitter_ms is None
    assert parsed.frame_width is None


def test_camel_case_mobile_stats_are_bounded_and_normalized():
    parsed = WebRTCStatsPayload.model_validate({
        "sentFps": 8,
        "packetsLost": 3,
        "jitterMs": 12.5,
        "frameWidth": 1280,
        "frameHeight": 720,
        "encodeMsPerFrame": 2.4,
        "jitterBufferDelayMs": None,
    })

    assert parsed.sent_fps == 8
    assert parsed.packet_loss == 3
    assert parsed.jitter_ms == 12.5


@pytest.mark.asyncio
async def test_stats_are_stored_only_for_current_authenticated_owner():
    sessions = SessionManager()
    connections = ConnectionManager()
    handler = MessageHandler(sessions, connections)
    socket = Socket()
    other = Socket()
    session = sessions.create_session("phone-1", "north")
    await connections.connect("phone-1", socket, generation=session.generation)
    message = {
        "type": "WEBRTC_STATS",
        "token": session.session_token,
        "payload": {
            "node_id": "phone-1",
            "direction": "north",
            "sentFps": 8,
        },
    }

    accepted = await handler.process_message(message, socket)
    rejected = await handler.process_message(message, other)

    assert accepted["type"] == "WEBRTC_STATS"
    assert session.transport == "webrtc"
    assert session.transport_stats["sent_fps"] == 8
    assert rejected["payload"]["error_code"] == "UNAUTHORIZED_SESSION"
    await handler.shutdown()


@pytest.mark.asyncio
async def test_out_of_range_stats_return_a_structured_error():
    sessions = SessionManager()
    connections = ConnectionManager()
    handler = MessageHandler(sessions, connections)
    socket = Socket()
    session = sessions.create_session("phone-1", "north")
    await connections.connect("phone-1", socket, generation=session.generation)

    response = await handler.process_message({
        "type": "WEBRTC_STATS",
        "token": session.session_token,
        "payload": {"node_id": "phone-1", "sentFps": 100_000},
    }, socket)

    assert response["payload"]["error_code"] == "INVALID_WEBRTC_STATS"
    assert session.transport_stats == {}
    await handler.shutdown()
