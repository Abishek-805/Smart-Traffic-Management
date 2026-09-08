"""
VehicleDetector runs vehicle detection and produces structured Detection objects.

Architecture note (Phase 3):
  - detect()           → calls model.predict()  (no track IDs) — kept for backward compat
  - detect_and_track() → calls model.track()    (single YOLO forward pass, includes ByteTrack IDs)

TrafficPipeline must use detect_and_track() exclusively. ByteTracker.update() then receives
the pre-computed tracked results and skips inference entirely.
"""

import time
from typing import List, Optional, Tuple
import numpy as np

from config.traffic import TARGET_CLASS_NAMES, normalize_vehicle_class
from ai.models.model_manager import ModelManager
from ai.detection.detection_types import Detection
from ai.utils.logger import get_logger

logger = get_logger("VehicleDetector")


class VehicleDetector:
    """
    Detector responsible for extracting vehicle bounding boxes from frames.
    Decoupled from visual rendering.
    """

    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager or ModelManager()
        model_names = getattr(self.model_manager.model, "names", {})
        if isinstance(model_names, list):
            model_names = dict(enumerate(model_names))
        self.vehicle_classes = {
            int(class_id): normalize_vehicle_class(class_name)
            for class_id, class_name in model_names.items()
            if normalize_vehicle_class(class_name) in TARGET_CLASS_NAMES
        }
        if not self.vehicle_classes:
            raise ValueError(
                "The selected model contains none of the supported traffic vehicle classes"
            )
        self.target_class_ids = sorted(self.vehicle_classes)
        logger.info("VehicleDetector model classes: %s", self.vehicle_classes)

    def detect(self, frame: np.ndarray, frame_number: int = 0, timestamp: float = 0.0) -> Tuple[List[Detection], float]:
        """
        Detect vehicles in frame using model.predict() (no track IDs).
        Preserved for backward compatibility, audit scripts, and unit tests.
        TrafficPipeline should use detect_and_track() instead.

        Returns:
            Tuple[List[Detection], float]: Detections and inference time in milliseconds.
        """
        start_time = time.perf_counter()
        results = self.model_manager.predict(frame, classes=self.target_class_ids)
        inference_time_ms = (time.perf_counter() - start_time) * 1000.0

        detections: List[Detection] = []
        if results and len(results) > 0:
            boxes = results[0].boxes
            if boxes is not None:
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    conf   = float(box.conf[0].item())
                    xyxy   = box.xyxy[0].cpu().numpy().astype(float)

                    if cls_id not in self.vehicle_classes or not np.isfinite(conf):
                        continue
                    height, width = frame.shape[:2]
                    if not np.all(np.isfinite(xyxy)):
                        continue
                    xyxy[[0, 2]] = np.clip(xyxy[[0, 2]], 0, width)
                    xyxy[[1, 3]] = np.clip(xyxy[[1, 3]], 0, height)
                    if xyxy[2] <= xyxy[0] or xyxy[3] <= xyxy[1]:
                        continue
                    xyxy = xyxy.astype(int)

                    class_name = self.vehicle_classes.get(cls_id, "vehicle")
                    bbox = (int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3]))

                    detection = Detection(
                        class_name=class_name,
                        class_id=cls_id,
                        confidence=conf,
                        bbox=bbox,
                        frame_number=frame_number,
                        timestamp=timestamp,
                    )
                    detections.append(detection)

        return detections, inference_time_ms

    def detect_and_track(
        self,
        frame: np.ndarray,
        frame_number: int = 0,
        timestamp: float = 0.0,
    ) -> Tuple[List[Detection], float]:
        """
        Single YOLO forward pass: detect vehicles AND assign ByteTrack IDs atomically.

        Replaces the previous two-call pattern:
            detector.detect(frame)  → model.predict()   [Inference #1 — eliminated]
            tracker.update(frame)   → model.track()     [Inference #2 — eliminated]
        Now collapsed to:
            detector.detect_and_track(frame) → model.track() [single inference only]

        Returns:
            Tuple[List[Detection], float]:
                - Detections with track_id populated from ByteTrack
                - Inference time in milliseconds
        """
        start_time = time.perf_counter()
        results = self.model_manager.track(frame, classes=self.target_class_ids)
        inference_time_ms = (time.perf_counter() - start_time) * 1000.0

        detections: List[Detection] = []

        if results and len(results) > 0:
            boxes = results[0].boxes
            if boxes is not None:
                xyxy_all = boxes.xyxy.cpu().numpy().astype(int)
                cls_all  = boxes.cls.int().cpu().tolist()
                conf_all = boxes.conf.cpu().numpy().tolist()
                ids_all  = (
                    boxes.id.int().cpu().tolist()
                    if boxes.id is not None
                    else [None] * len(cls_all)
                )

                for i in range(len(cls_all)):
                    cls_id     = cls_all[i]
                    if cls_id not in self.vehicle_classes or not np.isfinite(conf_all[i]):
                        continue
                    class_name = self.vehicle_classes.get(cls_id, "vehicle")
                    height, width = frame.shape[:2]
                    coords = np.asarray(xyxy_all[i], dtype=float)
                    if not np.all(np.isfinite(coords)):
                        continue
                    coords[[0, 2]] = np.clip(coords[[0, 2]], 0, width)
                    coords[[1, 3]] = np.clip(coords[[1, 3]], 0, height)
                    if coords[2] <= coords[0] or coords[3] <= coords[1]:
                        continue
                    bbox = (
                        int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3]),
                    )
                    conf     = float(conf_all[i])
                    track_id = int(ids_all[i]) if ids_all[i] is not None else None

                    detection = Detection(
                        class_name=class_name,
                        class_id=cls_id,
                        confidence=conf,
                        bbox=bbox,
                        track_id=track_id,
                        frame_number=frame_number,
                        timestamp=timestamp,
                    )
                    detections.append(detection)

        return detections, inference_time_ms
