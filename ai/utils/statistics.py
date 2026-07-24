"""
Statistics tracker module for tracking FPS, inference times, and performance metrics.
"""

import time
from collections import deque
from typing import Dict, Any


class StatisticsTracker:
    """
    Tracks real-time performance indicators such as FPS and inference latency.
    """

    def __init__(self, buffer_size: int = 30):
        self.buffer_size = buffer_size
        self.frame_count = 0
        self.start_time = time.time()
        self.last_frame_time = time.time()
        
        # Deques for moving window averages
        self.frame_durations = deque(maxlen=buffer_size)
        self.inference_durations = deque(maxlen=buffer_size)

    def record_frame(self, inference_time_ms: float) -> None:
        """
        Record a frame completion and its inference duration in milliseconds.
        """
        current_time = time.time()
        frame_duration = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        self.frame_count += 1
        if frame_duration > 0:
            self.frame_durations.append(frame_duration)
        self.inference_durations.append(inference_time_ms)

    @property
    def instant_fps(self) -> float:
        """Calculate FPS based on the most recent frame duration."""
        if not self.frame_durations or self.frame_durations[-1] <= 0:
            return 0.0
        return 1.0 / self.frame_durations[-1]

    @property
    def average_fps(self) -> float:
        """Calculate moving average FPS over the buffer size."""
        if not self.frame_durations:
            return 0.0
        avg_duration = sum(self.frame_durations) / len(self.frame_durations)
        return 1.0 / avg_duration if avg_duration > 0 else 0.0

    @property
    def average_inference_time_ms(self) -> float:
        """Calculate moving average inference time in milliseconds."""
        if not self.inference_durations:
            return 0.0
        return sum(self.inference_durations) / len(self.inference_durations)

    def get_summary(self) -> Dict[str, Any]:
        """
        Return a summary dict of execution statistics.
        """
        total_elapsed = time.time() - self.start_time
        return {
            "total_frames": self.frame_count,
            "elapsed_seconds": round(total_elapsed, 2),
            "average_fps": round(self.average_fps, 1),
            "avg_inference_ms": round(self.average_inference_time_ms, 2),
        }
