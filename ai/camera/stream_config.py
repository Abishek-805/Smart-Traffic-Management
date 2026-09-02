"""
Stream Configuration module defining camera stream sources (video files, RTSP/HTTP endpoints, webcam IDs)
and explicit validation helpers.
"""

import os
from pathlib import Path
from typing import Dict, Union

# Optional real USB/RTSP/file sources. Mobile WebSocket cameras require no
# entries here. Example: TRAFFIC_NORTH_SOURCE=rtsp://camera.local/stream
STREAM_CONFIG: Dict[str, Union[str, int, Path]] = {}
for _direction in ("north", "east", "south", "west"):
    _source = os.getenv(f"TRAFFIC_{_direction.upper()}_SOURCE")
    if _source:
        STREAM_CONFIG[_direction] = int(_source) if _source.isdigit() else _source


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
                        f"Configure an existing real video, USB index, or RTSP/HTTP stream."
                    )
