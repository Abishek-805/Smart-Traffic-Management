"""
Extensible, strongly-typed startup configuration dataclasses for Smart Traffic Management System.
Encapsulates versioning, camera acquisition, ESP32 hardware interface, runtime options, and debug flags.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Union, Optional
from pathlib import Path


@dataclass
class CameraConfig:
    """
    Configuration container for 4-camera video sources.
    Modes: 'mobile', 'usb', 'rtsp', 'webcam', 'demo'
    """
    mode: str = "mobile"
    sources: Dict[str, Union[str, int]] = field(default_factory=dict)

    def to_stream_config(self) -> Dict[str, Union[str, int]]:
        """Return stream sources dictionary for CameraManager."""
        return self.sources

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "sources": self.sources,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CameraConfig":
        return cls(
            mode=data.get("mode", "mobile"),
            sources=data.get("sources", {}),
        )


@dataclass
class HardwareConfig:
    """
    Configuration container for ESP32 serial hardware connection.
    """
    port: Optional[str] = None
    simulation: bool = True
    baudrate: int = 115200

    def to_dict(self) -> Dict[str, Any]:
        return {
            "port": self.port,
            "simulation": self.simulation,
            "baudrate": self.baudrate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HardwareConfig":
        return cls(
            port=data.get("port"),
            simulation=data.get("simulation", True),
            baudrate=data.get("baudrate", 115200),
        )


@dataclass
class RuntimeConfig:
    """
    Configuration container for system runtime execution parameters.
    """
    show_dashboard: bool = True
    save_output_video: bool = True
    save_logs: bool = True
    max_fps: int = 30

    def to_dict(self) -> Dict[str, Any]:
        return {
            "show_dashboard": self.show_dashboard,
            "save_output_video": self.save_output_video,
            "save_logs": self.save_logs,
            "max_fps": self.max_fps,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeConfig":
        return cls(
            show_dashboard=data.get("show_dashboard", True),
            save_output_video=data.get("save_output_video", True),
            save_logs=data.get("save_logs", True),
            max_fps=data.get("max_fps", 30),
        )


@dataclass
class DebugConfig:
    """
    Configuration container for developer diagnostic modes.
    """
    debug_mode: bool = False
    verbose_logging: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "debug_mode": self.debug_mode,
            "verbose_logging": self.verbose_logging,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DebugConfig":
        return cls(
            debug_mode=data.get("debug_mode", False),
            verbose_logging=data.get("verbose_logging", True),
        )


@dataclass
class StartupConfig:
    """
    Unified application configuration object containing schema versioning,
    camera acquisition settings, hardware settings, runtime options, and debug flags.
    """
    version: int = 1
    camera: CameraConfig = field(default_factory=CameraConfig)
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    debug: DebugConfig = field(default_factory=DebugConfig)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "camera": self.camera.to_dict(),
            "hardware": self.hardware.to_dict(),
            "runtime": self.runtime.to_dict(),
            "debug": self.debug.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StartupConfig":
        version = data.get("version", 1)
        cam_data = data.get("camera", data.get("camera_config", {}))
        hw_data = data.get("hardware", data.get("hardware_config", {}))
        rt_data = data.get("runtime", {})
        dbg_data = data.get("debug", {})

        return cls(
            version=version,
            camera=CameraConfig.from_dict(cam_data),
            hardware=HardwareConfig.from_dict(hw_data),
            runtime=RuntimeConfig.from_dict(rt_data),
            debug=DebugConfig.from_dict(dbg_data),
        )
