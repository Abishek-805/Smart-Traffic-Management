"""
Server package providing FastAPI WebSocket server, ConnectionManager, SessionManager, and Protocol schemas.
"""

from server.config import HOST, PORT, PROTOCOL_VERSION, HEARTBEAT_TIMEOUT_SEC, SESSION_EXPIRY_SEC
from server.protocol import (
    MessageType,
    BaseMessage,
    CameraRegistrationPayload,
    RegistrationAckPayload,
    HeartbeatPayload,
    HeartbeatAckPayload,
    DisconnectPayload,
    ErrorPayload,
    RegistrationMessage,
    RegistrationAckMessage,
    HeartbeatMessage,
    HeartbeatAckMessage,
    DisconnectMessage,
    ErrorMessage,
)
from server.session_manager import SessionManager, NodeSession
from server.connection_manager import ConnectionManager
from server.message_handler import MessageHandler
from server.websocket_server import app, get_app

__all__ = [
    "HOST",
    "PORT",
    "PROTOCOL_VERSION",
    "HEARTBEAT_TIMEOUT_SEC",
    "SESSION_EXPIRY_SEC",
    "MessageType",
    "BaseMessage",
    "CameraRegistrationPayload",
    "RegistrationAckPayload",
    "HeartbeatPayload",
    "HeartbeatAckPayload",
    "DisconnectPayload",
    "ErrorPayload",
    "RegistrationMessage",
    "RegistrationAckMessage",
    "HeartbeatMessage",
    "HeartbeatAckMessage",
    "DisconnectMessage",
    "ErrorMessage",
    "SessionManager",
    "NodeSession",
    "ConnectionManager",
    "MessageHandler",
    "app",
    "get_app",
]
