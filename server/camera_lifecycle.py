"""Truthful camera lifecycle derived from independent connection facts."""

from dataclasses import asdict, dataclass
from enum import Enum
import time
from typing import Optional


class CameraLifecycleState(str, Enum):
    OFFLINE = "OFFLINE"
    PAIRING = "PAIRING"
    CONNECTING = "CONNECTING"
    LIVE = "LIVE"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    RECONNECTING = "RECONNECTING"


@dataclass
class CameraStatusSnapshot:
    authenticated: bool = False
    pairing_active: bool = False
    transport_alive: bool = False
    media_connected: bool = False
    last_frame_at: Optional[float] = None
    last_inference_at: Optional[float] = None
    inference_fresh_sec: float = 3.0
    reconnecting: bool = False
    error_code: Optional[str] = None

    def derive_state(self, now: Optional[float] = None) -> CameraLifecycleState:
        current = time.monotonic() if now is None else now
        if self.error_code:
            return CameraLifecycleState.ERROR
        if self.reconnecting:
            return CameraLifecycleState.RECONNECTING
        if not self.authenticated:
            return (
                CameraLifecycleState.PAIRING
                if self.pairing_active
                else CameraLifecycleState.OFFLINE
            )
        if not self.transport_alive or not self.media_connected or self.last_frame_at is None:
            return CameraLifecycleState.CONNECTING
        if (
            self.last_inference_at is None
            or current - self.last_inference_at > self.inference_fresh_sec
        ):
            return CameraLifecycleState.DEGRADED
        return CameraLifecycleState.LIVE

    @property
    def state(self) -> CameraLifecycleState:
        return self.derive_state()

    @classmethod
    def from_session(cls, session) -> "CameraStatusSnapshot":
        return cls(
            authenticated=True,
            transport_alive=bool(getattr(session, "transport_alive", False)),
            media_connected=bool(getattr(session, "media_connected", False)),
            last_frame_at=getattr(session, "last_frame_at", None),
            last_inference_at=getattr(session, "last_inference_at", None),
            reconnecting=bool(getattr(session, "reconnecting", False)),
            error_code=getattr(session, "error_code", None),
        )

    def to_dict(self, now: Optional[float] = None) -> dict:
        result = asdict(self)
        result["state"] = self.derive_state(now).value
        return result
