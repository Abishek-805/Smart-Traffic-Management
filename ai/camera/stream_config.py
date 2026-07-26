"""
Stream Configuration module defining camera stream sources (video files, RTSP/HTTP endpoints, webcam IDs)
and explicit validation helpers.
"""

from pathlib import Path
from typing import Dict, Union
from config.paths import VIDEOS_DIR

NORTH = str(VIDEOS_DIR / "north.mp4")
SOUTH = str(VIDEOS_DIR / "south.mp4")
EAST = str(VIDEOS_DIR / "east.mp4")
WEST = str(VIDEOS_DIR / "west.mp4")

# Dictionary mapping lane names to stream sources
STREAM_CONFIG: Dict[str, Union[str, int, Path]] = {
    "north": NORTH,
    "south": SOUTH,
    "east": EAST,
    "west": WEST,
}


def validate_stream_sources(config: Dict[str, Union[str, int, Path]]) -> None:
    """
    Validates stream source existence for local video files.
    If a video file source is missing, raises a descriptive FileNotFoundError.
    Webcams (integers) and network URLs (http/rtsp) pass through validation.
    """
    for lane_name, source in config.items():
        if isinstance(source, (str, Path)):
            source_str = str(source)
            # Check if source represents a local file path rather than a URL or stream
            if not (source_str.startswith("http://") or source_str.startswith("https://") or source_str.startswith("rtsp://")):
                path = Path(source)
                if not path.is_file():
                    raise FileNotFoundError(
                        f"❌ [Camera Configuration Error] Stream source for camera '{lane_name}' "
                        f"was not found at '{path}'.\n"
                        f"Please place '{path.name}' inside the '{VIDEOS_DIR}' directory or run "
                        f"'python videos/generate_sample_video.py' to generate developer sample feeds."
                    )
