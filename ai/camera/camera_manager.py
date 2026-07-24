"""
CameraManager manages video stream acquisition, frame extraction, and video metadata.
"""

from pathlib import Path
from typing import Tuple, Optional, Union
import cv2
import numpy as np

from config.paths import DEFAULT_VIDEO_PATH
from ai.utils.logger import get_logger

logger = get_logger("CameraManager")


class CameraManager:
    """
    Manages continuous video stream ingestion from video files or webcam inputs.
    """

    def __init__(self, source: Union[str, Path, int] = DEFAULT_VIDEO_PATH):
        self.source = str(source) if isinstance(source, Path) else source
        self.cap: Optional[cv2.VideoCapture] = None
        self.frame_number = 0

        self._open_stream()

    def _open_stream(self) -> None:
        """Initialize OpenCV VideoCapture."""
        logger.info(f"Opening video source: '{self.source}'...")
        self.cap = cv2.VideoCapture(self.source)

        if not self.cap.isOpened():
            logger.error(f"Failed to open video source: '{self.source}'")
            raise ValueError(f"Could not open video stream at: {self.source}")

        logger.info(f"Stream opened successfully. Resolution: {self.resolution}, FPS: {self.fps:.1f}")

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray], int, float]:
        """
        Fetch the next frame from the stream.
        
        Returns:
            Tuple[bool, Optional[np.ndarray], int, float]:
                (success, frame_image, frame_number, timestamp_seconds)
        """
        if not self.is_opened():
            return False, None, self.frame_number, 0.0

        ret, frame = self.cap.read()
        if not ret:
            logger.info("Reached end of video stream or lost connection.")
            return False, None, self.frame_number, 0.0

        self.frame_number += 1
        timestamp = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

        return True, frame, self.frame_number, timestamp

    def is_opened(self) -> bool:
        """Check if video stream capture is active."""
        return self.cap is not None and self.cap.isOpened()

    @property
    def fps(self) -> float:
        """Get source stream nominal FPS."""
        if not self.cap:
            return 30.0
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        return fps if fps > 0 else 30.0

    @property
    def resolution(self) -> Tuple[int, int]:
        """Get source stream frame resolution (width, height)."""
        if not self.cap:
            return (0, 0)
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (width, height)

    @property
    def total_frames(self) -> int:
        """Get total number of frames in video file."""
        if not self.cap:
            return 0
        return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def release(self) -> None:
        """Release VideoCapture resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            logger.info("Video stream released successfully.")
