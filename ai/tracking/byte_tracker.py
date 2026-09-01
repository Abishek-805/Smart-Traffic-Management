"""Independent ByteTrack state for one camera; association never runs inference."""
from dataclasses import replace
from types import SimpleNamespace
from typing import List, Optional
import numpy as np
from ultralytics.engine.results import Boxes
from ultralytics.trackers.byte_tracker import BYTETracker
from ai.tracking.base_tracker import BaseTracker
from ai.detection.detection_types import Detection


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
            track_high_thresh=0.25, track_low_thresh=0.1, new_track_thresh=0.25,
            track_buffer=30, match_thresh=0.8, fuse_score=True,
        ))

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
                    frame_number=frame_number, timestamp=timestamp))
        return tracked
