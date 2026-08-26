from enum import Enum


class EventTypes(str, Enum):
    """Canonical cross-service event types for Redis Pub/Sub communication."""
    TELEMETRY_UPDATED = "system.telemetry.updated"
    CAMERA_REGISTERED = "camera.registered"
    CAMERA_DISCONNECTED = "camera.disconnected"
    FRAME_PROCESSED = "frame.processed"
    SYSTEM_COMMAND = "system.command"
    LOG_CREATED = "log.created"
