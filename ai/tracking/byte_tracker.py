"""Independent ByteTrack state for one camera; association never runs inference."""
from dataclasses import replace
import copy
from types import SimpleNamespace
from typing import List, Optional
import numpy as np
from ultralytics.engine.results import Boxes
from ultralytics.trackers.byte_tracker import BYTETracker
from ai.tracking.base_tracker import BaseTracker
from ai.detection.detection_types import Detection, ObservationState
from config.model import (
    TRACK_HIGH_THRESHOLD,
    TRACK_LOW_THRESHOLD,
    NEW_TRACK_THRESHOLD,
    TRACK_BUFFER_FRAMES,
    TRACK_MATCH_THRESHOLD,
    DETECTOR_FPS,
)


class CameraBYTETracker(BYTETracker):
    @staticmethod
    def reset_id():
        # Ultralytics IDs are global. Initializing a later camera must not rewind
        # IDs that an existing camera still uses.
        pass


class ByteTracker(BaseTracker):
    def __init__(self, model_manager=None):
        self.model_manager = model_manager
        self.tracker = CameraBYTETracker(SimpleNamespace(
            track_high_thresh=TRACK_HIGH_THRESHOLD,
            track_low_thresh=TRACK_LOW_THRESHOLD,
            new_track_thresh=NEW_TRACK_THRESHOLD,
            track_buffer=TRACK_BUFFER_FRAMES,
            match_thresh=TRACK_MATCH_THRESHOLD,
            fuse_score=True,
        ))
        self._last_by_track_id = {}
        self._prediction_horizon = 0
        self._observation_timestamp = None
        self._observation_interval = 1.0 / DETECTOR_FPS

    def update(self, detections: List[Detection], frame: Optional[np.ndarray] = None,
               frame_number: int = 0, timestamp: float = 0.0) -> List[Detection]:
        rows = np.asarray([(*d.bbox, d.confidence, d.class_id) for d in detections],
                          dtype=np.float32).reshape(-1, 6)
        shape = frame.shape[:2] if frame is not None else (720, 1280)
        tracks = self.tracker.update(Boxes(rows, orig_shape=shape), img=frame)
        tracked = []
        for row in tracks:
            index = int(row[-1])
            if 0 <= index < len(detections):
                tracked.append(replace(detections[index], track_id=int(row[4]),
                    bbox=tuple(int(v) for v in row[:4]),
                    frame_number=frame_number, timestamp=timestamp,
                    observation_type=ObservationState.OBSERVED))
        self._prediction_horizon = 0
        if self._observation_timestamp is not None and timestamp > self._observation_timestamp:
            self._observation_interval = timestamp - self._observation_timestamp
        self._observation_timestamp = timestamp
        self._last_by_track_id = {d.track_id: d for d in tracked if d.track_id is not None}
        return tracked

    def predict(self, frame_number: int = 0, timestamp: float = 0.0) -> List[Detection]:
        """Project active tracks without submitting a fake detector observation."""
        if self._observation_timestamp is None:
            return []
        elapsed = timestamp - self._observation_timestamp
        # Kalman velocity is measured per detector observation, not preview frame.
        # Never keep phantom vehicles alive indefinitely when input disappears.
        if elapsed < 0 or elapsed > min(2.0, TRACK_BUFFER_FRAMES / DETECTOR_FPS):
            return []
        steps = elapsed / max(self._observation_interval, 1e-3)
        projected = copy.deepcopy([
            track for track in self.tracker.tracked_stracks
            if getattr(track, "is_activated", False)
        ])
        for track in projected:
            # Only project display coordinates. Canonical mean/covariance remain
            # untouched for ByteTrack's next real observation and association.
            track.mean[:4] += track.mean[4:] * steps
        output = []
        for track in projected:
            previous = self._last_by_track_id.get(int(track.track_id))
            if previous is None:
                continue
            bbox = tuple(int(round(v)) for v in track.xyxy)
            output.append(replace(
                previous, bbox=bbox, frame_number=frame_number, timestamp=timestamp,
                observation_type=ObservationState.PREDICTED,
            ))
        return output
