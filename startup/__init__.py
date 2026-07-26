"""
Startup package providing application banner, StartupManager orchestrator, configuration dataclasses,
camera setup wizard, hardware COM port setup wizard, profile persistence, and configuration validation.
"""

from startup.banner import display_banner
from startup.startup_config import (
    StartupConfig,
    CameraConfig,
    HardwareConfig,
    RuntimeConfig,
    DebugConfig,
)
from startup.startup_manager import StartupManager
from startup.camera_setup import setup_camera_config
from startup.hardware_setup import setup_hardware_config, discover_com_ports
from startup.profile_manager import load_profile, save_profile, prompt_use_existing_profile
from startup.validator import ConfigValidator


def run_startup_wizard(interactive: bool = True) -> StartupConfig:
    """Convenience alias delegating to StartupManager.run()."""
    return StartupManager.run(interactive=interactive)


__all__ = [
    "display_banner",
    "StartupManager",
    "StartupConfig",
    "CameraConfig",
    "HardwareConfig",
    "RuntimeConfig",
    "DebugConfig",
    "setup_camera_config",
    "setup_hardware_config",
    "discover_com_ports",
    "load_profile",
    "save_profile",
    "prompt_use_existing_profile",
    "ConfigValidator",
    "run_startup_wizard",
]
