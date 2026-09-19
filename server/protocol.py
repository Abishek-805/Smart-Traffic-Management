"""
Protocol schema definitions using Pydantic models and MessageType enum.
"""

from enum import Enum
import time
from typing import Optional, Dict, Any
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from server.config import PROTOCOL_VERSION


class MessageType(str, Enum):
    """Supported WebSocket message types."""
    REGISTER_CAMERA = "REGISTER_CAMERA"
    REGISTRATION_ACK = "REGISTRATION_ACK"
    HEARTBEAT = "HEARTBEAT"
    HEARTBEAT_ACK = "HEARTBEAT_ACK"
    DISCONNECT = "DISCONNECT"
    ERROR = "ERROR"
    VIDEO_FRAME = "VIDEO_FRAME"
    WEBRTC_OFFER = "WEBRTC_OFFER"
    WEBRTC_STOP = "WEBRTC_STOP"
    WEBRTC_STATS = "WEBRTC_STATS"
    START_STREAM = "START_STREAM"
    STOP_STREAM = "STOP_STREAM"


class BaseMessage(BaseModel):
    """Base schema for all WebSocket protocol messages."""
    type: Optional[MessageType] = None
    message_type: Optional[MessageType] = None
    protocol_version: str = PROTOCOL_VERSION
    timestamp: float = Field(default_factory=time.time)
    id: Optional[str] = None  # Correlation ID for request/response matching

    def model_post_init(self, __context):
        if self.message_type is not None and self.type is None:
            self.type = self.message_type
        elif self.type is not None and self.message_type is None:
            self.message_type = self.type


# --- Payloads ---

class CameraRegistrationPayload(BaseModel):
    node_id: Optional[str] = "CAM-001"
    camera_direction: Optional[str] = "north"
    resolution: Optional[str] = "1280x720"
    fps: Optional[float] = None
    device_info: Optional[str] = None
    session: Optional[str] = None
    device: Optional[Any] = None
    capabilities: Optional[Any] = None


class RegistrationAckPayload(BaseModel):
    node_id: str
    session_token: str
    status: str = "CONNECTED"
    assigned_direction: str = "north"
    assignedLane: Optional[str] = "North Intersection - Lane 1"
    cameraId: Optional[str] = None
    message: str = "Registration successful"


class VideoFramePayload(BaseModel):
    node_id: Optional[str] = None
    direction: Optional[str] = "north"
    frame_data: str  # base64-encoded JPEG
    timestamp: Optional[float] = None


class StartStreamPayload(BaseModel):
    target_fps: Optional[int] = 15
    resolution: Optional[str] = "640x480"
    quality: Optional[int] = 50


class WebRTCStatsPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sent_fps: Optional[float] = Field(None, ge=0, le=240, validation_alias=AliasChoices("sent_fps", "sentFps"))
    packet_loss: Optional[int] = Field(None, ge=0, validation_alias=AliasChoices("packet_loss", "packetsLost"))
    jitter_ms: Optional[float] = Field(None, ge=0, le=60_000, validation_alias=AliasChoices("jitter_ms", "jitterMs"))
    frame_width: Optional[int] = Field(None, ge=1, le=16_384, validation_alias=AliasChoices("frame_width", "frameWidth"))
    frame_height: Optional[int] = Field(None, ge=1, le=16_384, validation_alias=AliasChoices("frame_height", "frameHeight"))
    encode_ms_per_frame: Optional[float] = Field(None, ge=0, le=60_000, validation_alias=AliasChoices("encode_ms_per_frame", "encodeMsPerFrame"))
    jitter_buffer_delay_ms: Optional[float] = Field(None, ge=0, le=60_000, validation_alias=AliasChoices("jitter_buffer_delay_ms", "jitterBufferDelayMs"))


class HeartbeatPayload(BaseModel):
    node_id: Optional[str] = None
    session_token: Optional[str] = None
    cameraId: Optional[str] = None
    uptime_sec: Optional[float] = 0.0


class HeartbeatAckPayload(BaseModel):
    node_id: str
    status: str = "OK"
    pingMs: Optional[float] = None


class DisconnectPayload(BaseModel):
    node_id: str
    session_token: str
    reason: Optional[str] = "Client graceful disconnect"


class ErrorPayload(BaseModel):
    node_id: Optional[str] = None
    error_code: str
    message: str
    direction: Optional[str] = None
    owner_state: Optional[str] = None
    retry_after_ms: Optional[int] = None


# --- Full Message Models ---

class RegistrationMessage(BaseMessage):
    message_type: MessageType = MessageType.REGISTER_CAMERA
    payload: CameraRegistrationPayload


class RegistrationAckMessage(BaseMessage):
    message_type: MessageType = MessageType.REGISTRATION_ACK
    payload: RegistrationAckPayload


class HeartbeatMessage(BaseMessage):
    message_type: MessageType = MessageType.HEARTBEAT
    payload: HeartbeatPayload


class HeartbeatAckMessage(BaseMessage):
    message_type: MessageType = MessageType.HEARTBEAT_ACK
    payload: HeartbeatAckPayload


class DisconnectMessage(BaseMessage):
    message_type: MessageType = MessageType.DISCONNECT
    payload: DisconnectPayload


class ErrorMessage(BaseMessage):
    message_type: MessageType = MessageType.ERROR
    payload: ErrorPayload
