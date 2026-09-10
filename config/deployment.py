"""Authoritative deployment profiles shared by capture, inference and telemetry."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from typing import Mapping


@dataclass(frozen=True)
class DeploymentProfile:
    """Effective bounded settings for one deployment target."""

    name: str
    validation_status: str
    hardware_mode: str
    serial_port: str | None
    serial_baudrate: int
    capture_fps: float
    webrtc_sample_fps: float
    detector_fps: float
    input_size: int
    batch_size: int
    cpu_threads: int
    preview_fps: float

    def to_telemetry(self) -> dict:
        """Return public profile values without fabricating measured capability."""
        return asdict(self)


_PROFILE_DEFAULTS = {
    "laptop": {
        "name": "LAPTOP",
        "validation_status": "MEASURED_LOCAL_SOFTWARE",
        "capture_fps": 4.0,
        "webrtc_sample_fps": 4.0,
        "detector_fps": 2.0,
        "input_size": 576,
        "batch_size": 4,
        "cpu_threads": 4,
        "preview_fps": 4.0,
    },
    "raspberry_pi": {
        "name": "RASPBERRY_PI",
        "validation_status": "PROPOSED_UNVALIDATED",
        "capture_fps": 2.0,
        "webrtc_sample_fps": 2.0,
        "detector_fps": 1.0,
        "input_size": 512,
        "batch_size": 1,
        "cpu_threads": 4,
        "preview_fps": 2.0,
    },
}


def _bounded_float(environ: Mapping[str, str], key: str, default: float,
                   minimum: float, maximum: float) -> float:
    value = float(environ.get(key, default))
    if not minimum <= value <= maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return value


def _bounded_int(environ: Mapping[str, str], key: str, default: int,
                 minimum: int, maximum: int) -> int:
    value = int(environ.get(key, default))
    if not minimum <= value <= maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return value


def load_deployment_profile(environ: Mapping[str, str] | None = None) -> DeploymentProfile:
    """Load and validate one effective runtime profile from environment values."""
    values: Mapping[str, str] = os.environ if environ is None else environ
    profile_key = values.get("TRAFFIC_PROFILE", "laptop").strip().lower()
    if profile_key not in _PROFILE_DEFAULTS:
        raise ValueError("TRAFFIC_PROFILE must be 'laptop' or 'raspberry_pi'")
    defaults = _PROFILE_DEFAULTS[profile_key]

    hardware_mode = values.get("HARDWARE", "simulation").strip().lower()
    if hardware_mode not in {"simulation", "esp32"}:
        raise ValueError("HARDWARE must be 'simulation' or 'esp32'")
    serial_port = values.get("ESP32_PORT", "").strip() or None
    if hardware_mode == "esp32" and serial_port is None:
        raise ValueError("ESP32_PORT is required when HARDWARE=esp32")

    batch_size = _bounded_int(values, "YOLO_BATCH_SIZE", defaults["batch_size"], 1, 4)
    model_name = values.get("YOLO_MODEL_NAME", "yolov8n.pt").lower()
    if "ncnn" in model_name:
        batch_size = 1

    return DeploymentProfile(
        name=defaults["name"],
        validation_status=defaults["validation_status"],
        hardware_mode=hardware_mode,
        serial_port=serial_port,
        serial_baudrate=_bounded_int(values, "ESP32_BAUDRATE", 115200, 1200, 4_000_000),
        capture_fps=_bounded_float(values, "CAMERA_CAPTURE_FPS", defaults["capture_fps"], 0.1, 30.0),
        webrtc_sample_fps=_bounded_float(values, "WEBRTC_SAMPLE_FPS", defaults["webrtc_sample_fps"], 0.1, 30.0),
        detector_fps=_bounded_float(values, "DETECTOR_FPS", defaults["detector_fps"], 0.1, 30.0),
        input_size=_bounded_int(values, "YOLO_INPUT_SIZE", defaults["input_size"], 320, 1280),
        batch_size=batch_size,
        cpu_threads=_bounded_int(values, "YOLO_CPU_THREADS", defaults["cpu_threads"], 1, 16),
        preview_fps=_bounded_float(values, "PREVIEW_FPS", defaults["preview_fps"], 0.1, 30.0),
    )


ACTIVE_PROFILE = load_deployment_profile()
