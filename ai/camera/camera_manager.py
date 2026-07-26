"""
CameraManager manages multiple CameraStream instances dynamically using dictionary-based collection logic.
"""

from pathlib import Path
from typing import Dict, Union, Optional, Tuple, Any
import numpy as np

from ai.camera.camera_stream import CameraStream
from ai.camera.stream_config import STREAM_CONFIG, validate_stream_sources
from ai.utils.logger import get_logger

logger = get_logger("CameraManager")


class CameraManager:
    """
    Manages continuous video stream ingestion across multiple camera sources
    (e.g., North, South, East, West approaches).
    """

    def __init__(self, config: Optional[Union[Dict[str, Union[str, int, Path]], str, Path]] = None):
        """
        Initialize CameraManager.
        
        Args:
            config: Optional stream source mapping dictionary or single source path.
                    Defaults to STREAM_CONFIG if None.
        """
        if config is None:
            config = STREAM_CONFIG
        elif isinstance(config, (str, Path)):
            # Wrap single source as 'north' for backward compatibility
            config = {"north": config}

        # Validate video files exist before starting streams
        validate_stream_sources(config)

        self.streams: Dict[str, CameraStream] = {}
        for lane_name, source in config.items():
            self.streams[lane_name] = CameraStream(source=source, lane_name=lane_name)

        logger.info(f"CameraManager initialized managing {len(self.streams)} stream(s): {list(self.streams.keys())}")

    def start_all(self) -> None:
        """Open and connect all camera streams."""
        logger.info("Starting all camera streams...")
        for stream in self.streams.values():
            if not stream.is_connected():
                stream.open()

    def stop_all(self) -> None:
        """Stop and release all camera streams."""
        logger.info("Stopping all camera streams...")
        for stream in self.streams.values():
            stream.release()

    def release(self) -> None:
        """Alias for stop_all to ensure resource cleanup interface consistency."""
        self.stop_all()

    def read_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Read next frame and metadata from all camera streams.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping lane name to rich stream payload:
                {
                    "north": {
                        "frame": frame_ndarray or None,
                        "connected": bool,
                        "fps": float,
                        "resolution": Tuple[int, int],
                        "timestamp": float,
                        "frame_number": int,
                        "lane_name": str,
                    },
                    ...
                }
        """
        results = {}
        for lane_name, stream in self.streams.items():
            success, frame, meta = stream.read()
            payload = dict(meta)
            payload["frame"] = frame
            results[lane_name] = payload
        return results

    def get_frames(self) -> Dict[str, Optional[np.ndarray]]:
        """
        Convenience method to retrieve raw frame images for all streams.
        
        Returns:
            Dict[str, Optional[np.ndarray]]: Dictionary mapping lane name to frame image array.
        """
        data = self.read_all()
        return {lane: item["frame"] for lane, item in data.items()}

    def get_status(self) -> Dict[str, bool]:
        """
        Get connection status for all camera streams.
        
        Returns:
            Dict[str, bool]: Dictionary mapping lane name to boolean connection state.
        """
        return {lane: stream.is_connected() for lane, stream in self.streams.items()}

    def get_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed camera health statistics across all streams.
        """
        health = {}
        for lane_name, stream in self.streams.items():
            health[lane_name] = {
                "connected": stream.is_connected(),
                "fps": round(stream.fps, 1),
                "resolution": stream.resolution,
                "frame_number": stream.frame_number,
                "source": stream.source,
            }
        return health

    # Backward compatibility methods for legacy single-stream callers
    def get_frame(self) -> Tuple[bool, Optional[np.ndarray], int, float]:
        """
        Legacy single-camera frame reader (reads primary stream).
        """
        primary_lane = next(iter(self.streams.keys())) if self.streams else "north"
        if primary_lane in self.streams:
            stream = self.streams[primary_lane]
            success, frame, meta = stream.read()
            return success, frame, meta["frame_number"], meta["timestamp"]
        return False, None, 0, 0.0

    @property
    def fps(self) -> float:
        """Get primary stream FPS."""
        if not self.streams:
            return 30.0
        primary_lane = next(iter(self.streams.keys()))
        return self.streams[primary_lane].fps

    @property
    def resolution(self) -> Tuple[int, int]:
        """Get primary stream resolution."""
        if not self.streams:
            return (1280, 720)
        primary_lane = next(iter(self.streams.keys()))
        return self.streams[primary_lane].resolution
