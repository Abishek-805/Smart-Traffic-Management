"""
ByteTracker — tracking-only adapter (Phase 3 architecture).

Architecture contract:
  - update() accepts Detection objects that ALREADY carry track_id values from VehicleDetector.detect_and_track().
  - It never invokes the YOLO model. Zero inference calls.
  - _update_with_inference() is kept as a private fallback for explicit use in tests/audit scripts
    that bypass the unified detect_and_track() pipeline.
"""

from typing import List, Dict, Optional, Tuple
import numpy as np

from ai.tracking.base_tracker import BaseTracker
from ai.detection.detection_types import Detection
from ai.models.model_manager import ModelManager
from config.traffic import TARGET_CLASS_IDS, VEHICLE_CLASSES
from ai.utils.logger import get_logger

logger = get_logger("ByteTracker")


class ByteTracker(BaseTracker):
    """
    Tracking-only adapter that normalises and validates pre-computed ByteTrack results.
    TrafficPipeline calls VehicleDetector.detect_and_track() (single YOLO pass),
    then passes the results directly to ByteTracker.update() — no re-inference.
    """

    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager or ModelManager()
        self.target_class_ids = list(TARGET_CLASS_IDS)
        logger.info("ByteTracker initialized (tracking-only mode — no inference).")

    def update(
        self,
        detections: List[Detection],
        frame: Optional[np.ndarray] = None,
        frame_number: int = 0,
        timestamp: float = 0.0,
    ) -> List[Detection]:
        """
        Accept pre-tracked detections (with track_id already assigned by detect_and_track()).
        Validates that all detections have a track_id; logs a warning for any that don't.
        Returns the detections unchanged — no model inference is performed.

        Falls back to _update_with_inference() ONLY if NO detections carry track_ids,
        which indicates the caller used the old detect() path (audit scripts, unit tests).
        """
        if not detections:
            return detections

        # Check whether track_ids are already populated (i.e. detect_and_track() was used)
        has_any_track_id = any(d.track_id is not None for d in detections)

        if has_any_track_id:
            # Fast path: track IDs already assigned — validate and return
            missing = [d for d in detections if d.track_id is None]
            if missing:
                logger.warning(
                    f"ByteTracker: {len(missing)}/{len(detections)} detections have no track_id "
                    f"in frame #{frame_number}. These are from low-confidence detections "
                    f"that ByteTrack could not associate to a track."
                )
            return detections

        # Fallback path: detections came from detect() (no track IDs) — run inference
        # This path is only reached by audit scripts and unit tests that use detect() directly.
        logger.debug(
            f"ByteTracker: no track_ids present in frame #{frame_number}. "
            f"Falling back to _update_with_inference() (detect() was used, not detect_and_track())."
        )
        if frame is not None:
            return self._update_with_inference(detections, frame, frame_number, timestamp)
        return detections

    def _update_with_inference(
        self,
        detections: List[Detection],
        frame: np.ndarray,
        frame_number: int = 0,
        timestamp: float = 0.0,
    ) -> List[Detection]:
        """
        Private fallback: run model.track() to assign track IDs when detect_and_track() was not used.
        Used by audit scripts, unit tests, and the Phase 2.5 integrity checker.
        NOT called by TrafficPipeline in production.
        """
        if frame is None or len(detections) == 0:
            return detections

        try:
            results = self.model_manager.model.track(
                source=frame,
                conf=self.model_manager.confidence,
                iou=self.model_manager.iou,
                classes=self.target_class_ids,
                persist=True,
                tracker="bytetrack.yaml",
                verbose=False,
            )

            if results and len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                if boxes.id is not None:
                    track_ids  = boxes.id.int().cpu().tolist()
                    xyxy_all   = boxes.xyxy.cpu().numpy().astype(int)
                    cls_all    = boxes.cls.int().cpu().tolist()
                    conf_all   = boxes.conf.cpu().numpy().tolist()

                    tracked: List[Detection] = []
                    for i, tid in enumerate(track_ids):
                        cls_id     = cls_all[i]
                        class_name = VEHICLE_CLASSES.get(cls_id, "vehicle")
                        bbox = (
                            int(xyxy_all[i][0]),
                            int(xyxy_all[i][1]),
                            int(xyxy_all[i][2]),
                            int(xyxy_all[i][3]),
                        )
                        conf = float(conf_all[i])
                        tracked.append(Detection(
                            class_name=class_name,
                            class_id=cls_id,
                            confidence=conf,
                            bbox=bbox,
                            track_id=tid,
                            frame_number=frame_number,
                            timestamp=timestamp,
                        ))
                    return tracked

        except Exception as e:
            logger.warning(f"ByteTracker._update_with_inference error: {e}. Returning raw detections.", exc_info=False)

        return detections
