"""
Hardware interface package providing CommandEncoder, ESP32Interface, and HardwareStatus.
"""

from ai.hardware.command_encoder import CommandEncoder
from ai.hardware.esp32_interface import (
    ESP32Interface,
    HardwareConnectionState,
    HardwareStatus,
    hardware_is_safe_to_run,
)

__all__ = [
    "CommandEncoder",
    "ESP32Interface",
    "HardwareConnectionState",
    "HardwareStatus",
    "hardware_is_safe_to_run",
]
