"""
Camera package providing CameraStream, CameraManager, and stream configurations.
"""

from ai.camera.camera_stream import CameraStream
from ai.camera.camera_manager import CameraManager
from ai.camera.stream_config import (
    STREAM_CONFIG,
    NORTH,
    SOUTH,
    EAST,
    WEST,
    validate_stream_sources,
)

__all__ = [
    "CameraStream",
    "CameraManager",
    "STREAM_CONFIG",
    "NORTH",
    "SOUTH",
    "EAST",
    "WEST",
    "validate_stream_sources",
]
