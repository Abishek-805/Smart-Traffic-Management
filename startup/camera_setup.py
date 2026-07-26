"""
CameraSetup wizard for interactive selection of mobile IP streams, USB cameras, RTSP streams, webcam, or demo videos.
"""

from typing import Dict, Union
from pathlib import Path
from config.paths import VIDEOS_DIR
from startup.startup_config import CameraConfig
from ai.utils.logger import get_logger

logger = get_logger("CameraSetup")


def setup_camera_config() -> CameraConfig:
    """
    Interactively prompt user to select camera stream sources for North, South, East, and West lanes.

    Returns:
        CameraConfig object containing mode and stream sources dict.
    """
    print("\n==================================================")
    print(" 🎥 SELECT CAMERA INPUT SOURCES")
    print("==================================================")
    print(" 1. Mobile IP Cameras  (e.g., http://192.168.1.50:8080/video)")
    print(" 2. USB Cameras        (Device indices e.g., 0, 1, 2, 3)")
    print(" 3. RTSP Streams       (e.g., rtsp://admin:pass@192.168.1.x:554)")
    print(" 4. Primary Webcam     (Single camera split feed)")
    print(" 5. Demo Videos        (Development & testing MP4 files)")
    print("==================================================")

    choice = ""
    try:
        choice = input("Enter choice [1-5] (default: 5): ").strip()
    except (EOFError, KeyboardInterrupt):
        choice = "5"

    if choice == "1":
        return _configure_mobile_cameras()
    elif choice == "2":
        return _configure_usb_cameras()
    elif choice == "3":
        return _configure_rtsp_cameras()
    elif choice == "4":
        return _configure_webcam()
    else:
        return _configure_demo_videos()


def _configure_mobile_cameras() -> CameraConfig:
    """Prompt user for Mobile IP stream URLs for 4 camera directions."""
    print("\n--- Configure Mobile IP Cameras ---")
    sources: Dict[str, Union[str, int]] = {}
    lanes = ["north", "south", "east", "west"]

    for lane in lanes:
        default_url = f"http://192.168.1.10{lanes.index(lane) + 1}:8080/video"
        try:
            val = input(f" {lane.capitalize():<6} Camera URL [{default_url}]: ").strip()
            sources[lane] = val if val else default_url
        except (EOFError, KeyboardInterrupt):
            sources[lane] = default_url

    return CameraConfig(mode="mobile", sources=sources)


def _configure_usb_cameras() -> CameraConfig:
    """Prompt user for USB camera device indices for 4 camera directions."""
    print("\n--- Configure USB Cameras ---")
    sources: Dict[str, Union[str, int]] = {}
    lanes = ["north", "south", "east", "west"]

    for idx, lane in enumerate(lanes):
        try:
            val = input(f" {lane.capitalize():<6} Camera Index [{idx}]: ").strip()
            sources[lane] = int(val) if val.isdigit() else idx
        except (EOFError, KeyboardInterrupt):
            sources[lane] = idx

    return CameraConfig(mode="usb", sources=sources)


def _configure_rtsp_cameras() -> CameraConfig:
    """Prompt user for RTSP stream URLs for 4 camera directions."""
    print("\n--- Configure RTSP Cameras ---")
    sources: Dict[str, Union[str, int]] = {}
    lanes = ["north", "south", "east", "west"]

    for idx, lane in enumerate(lanes):
        default_url = f"rtsp://192.168.1.10{idx + 1}:554/stream1"
        try:
            val = input(f" {lane.capitalize():<6} RTSP Stream URL [{default_url}]: ").strip()
            sources[lane] = val if val else default_url
        except (EOFError, KeyboardInterrupt):
            sources[lane] = default_url

    return CameraConfig(mode="rtsp", sources=sources)


def _configure_webcam() -> CameraConfig:
    """Prompt user for primary webcam index."""
    print("\n--- Configure Primary Webcam ---")
    cam_idx = 0
    try:
        val = input(" Primary Webcam Device Index [0]: ").strip()
        cam_idx = int(val) if val.isdigit() else 0
    except (EOFError, KeyboardInterrupt):
        cam_idx = 0

    sources: Dict[str, Union[str, int]] = {
        "north": cam_idx,
        "south": cam_idx,
        "east": cam_idx,
        "west": cam_idx,
    }
    return CameraConfig(mode="webcam", sources=sources)


def _configure_demo_videos() -> CameraConfig:
    """Configure standard development MP4 videos."""
    print("\n--- Loading Demo Video Feeds ---")
    sources: Dict[str, Union[str, int]] = {
        "north": str(VIDEOS_DIR / "north.mp4"),
        "south": str(VIDEOS_DIR / "south.mp4"),
        "east": str(VIDEOS_DIR / "east.mp4"),
        "west": str(VIDEOS_DIR / "west.mp4"),
    }
    return CameraConfig(mode="demo", sources=sources)
