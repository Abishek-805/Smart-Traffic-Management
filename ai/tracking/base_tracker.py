"""
Base abstract interface for object tracking algorithms (e.g., ByteTrack, SORT).
"""

from abc import ABC, abstractmethod
from typing import List
from ai.detection.detection_types import Detection


class BaseTracker(ABC):
    """
    Abstract interface for object tracking.
    In Sprint 2, ByteTracker will implement this interface.
    """

    @abstractmethod
    def update(self, detections: List[Detection], frame_number: int = 0, timestamp: float = 0.0) -> List[Detection]:
        """
        Update tracker state with new frame detections.
        
        Args:
            detections: List of Detection objects without track IDs.
            frame_number: Current video frame index.
            timestamp: Frame timestamp in seconds.
            
        Returns:
            List[Detection]: Detection objects with updated track_id values.
        """
        raise NotImplementedError("Subclasses must implement update()")


class PassThroughTracker(BaseTracker):
    """
    Sprint 1 placeholder tracker that passes detections through unaltered.
    """

    def update(self, detections: List[Detection], frame_number: int = 0, timestamp: float = 0.0) -> List[Detection]:
        return detections
