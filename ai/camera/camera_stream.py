"""
CameraStream handles an individual camera stream, webcam, or video file source.
"""

from pathlib import Path
import time
from typing import Tuple, Optional, Union, Dict, Any
import cv2
import numpy as np

from ai.utils.logger import get_logger

logger = get_logger("CameraStream")


class CameraStream:
    """
    Handles a single camera stream, IP camera URL, or video file source.
    """

    def __init__(self, source: Union[str, int, Path], lane_name: str = "camera"):
        self.source = str(source) if isinstance(source, Path) else source
        self.lane_name = lane_name
        self.capture: Optional[cv2.VideoCapture] = None
        self.connected: bool = False
        self.fps: Optional[float] = None
        self.resolution: Tuple[int, int] = (0, 0)
        self.frame: Optional[np.ndarray] = None
        self.frame_number: int = 0
        self.timestamp: float = 0.0

        # Attempt to open the camera stream upon creation
        self.open()

    def open(self) -> bool:
        """
        Open the video source stream and query metadata.
        """
        logger.info(f"Opening camera stream '{self.lane_name}' from source: '{self.source}'...")
        try:
            self.capture = cv2.VideoCapture(self.source)
            if self.capture is not None and self.capture.isOpened():
                self.connected = True
                
                # Fetch FPS metadata
                cam_fps = self.capture.get(cv2.CAP_PROP_FPS)
                self.fps = cam_fps if (cam_fps is not None and cam_fps > 0) else None
                
                # Fetch Resolution metadata (width, height)
                width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.resolution = (width, height)

                logger.info(
                    f"✅ Camera '{self.lane_name}' connected successfully. "
                    f"Resolution: {width}x{height}, FPS: "
                    f"{f'{self.fps:.1f}' if self.fps is not None else 'UNAVAILABLE'}"
                )
                return True
            else:
                self.connected = False
                logger.error(f"❌ Failed to open camera stream '{self.lane_name}' at '{self.source}'.")
                return False
        except Exception as e:
            self.connected = False
            logger.error(f"❌ Exception while opening camera '{self.lane_name}': {e}")
            return False

    def read(self) -> Tuple[bool, Optional[np.ndarray], Dict[str, Any]]:
        """
        Read the next frame from the camera stream along with metadata.
        Automatically loops video file sources upon reaching EOF.

        Returns:
            Tuple[bool, Optional[np.ndarray], Dict[str, Any]]:
                (success, frame_ndarray, metadata_dict)
        """
        if not self.is_connected() or self.capture is None:
            # Try reconnecting if currently disconnected
            if not self.open():
                return False, None, self._get_metadata(success=False)

        ret, frame = self.capture.read()

        # Handle End-Of-File for local video streams (auto-looping)
        if not ret:
            # Check if this is a video file source that reached EOF
            if isinstance(self.source, str) and not (
                self.source.startswith("http://")
                or self.source.startswith("https://")
                or self.source.startswith("rtsp://")
                or self.source.isdigit()
            ):
                # Rewind video stream to start
                self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.capture.read()

        if not ret or frame is None:
            self.connected = False
            self.frame = None
            logger.warning(f"⚠️ Camera '{self.lane_name}' dropped frame or stream interrupted.")
            return False, None, self._get_metadata(success=False)

        self.connected = True
        self.frame = frame
        self.frame_number += 1
        self.timestamp = time.time()

        return True, self.frame, self._get_metadata(success=True)

    def is_connected(self) -> bool:
        """Check if camera capture stream is active."""
        return self.connected and self.capture is not None and self.capture.isOpened()

    def release(self) -> None:
        """Release VideoCapture resources."""
        if self.capture is not None:
            try:
                self.capture.release()
            except Exception as e:
                logger.error(f"Error releasing camera '{self.lane_name}': {e}")
            finally:
                self.capture = None
        self.connected = False
        self.frame = None
        logger.info(f"Camera stream '{self.lane_name}' released successfully.")

    def _get_metadata(self, success: bool) -> Dict[str, Any]:
        """Generate structured frame metadata dictionary."""
        return {
            "lane_name": self.lane_name,
            "connected": self.connected and success,
            "fps": round(self.fps, 1) if self.fps is not None else None,
            "resolution": self.resolution,
            "frame_number": self.frame_number,
            "timestamp": self.timestamp if success else time.time(),
            "source": self.source,
        }
