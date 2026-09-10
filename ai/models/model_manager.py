"""
ModelManager handles vision model initialization, device selection, and abstraction over inference engines.
"""

import os
import threading
import torch
import cv2
import numpy as np
import time
from pathlib import Path
from typing import Any, Union, Dict
from ultralytics import YOLO

from config.model import (
    MODEL_NAME,
    CONFIDENCE_THRESHOLD,
    IOU_THRESHOLD,
    DEVICE,
    INPUT_SIZE,
    MAX_DETECTIONS,
    CPU_THREADS,
)
from config.paths import MODELS_DIR
from ai.utils.logger import get_logger

logger = get_logger("ModelManager")


class ModelManager:
    """
    Manages loading, initializing, and serving YOLO vision models.
    """

    def __init__(
        self,
        model_name: str = MODEL_NAME,
        confidence: float = CONFIDENCE_THRESHOLD,
        iou: float = IOU_THRESHOLD,
        device: str = DEVICE,
        input_size: int = INPUT_SIZE,
        max_detections: int = MAX_DETECTIONS,
    ):
        self.model_name = model_name
        self.confidence = confidence
        self.iou = iou
        self.device = device
        self.input_size = input_size
        self.max_detections = max_detections
        self.cpu_threads = CPU_THREADS
        cv2.setNumThreads(1)
        if not torch.cuda.is_available() or self.device == "cpu":
            torch.set_num_threads(self.cpu_threads)
            try:
                torch.set_num_interop_threads(1)
            except RuntimeError:
                # PyTorch permits configuring the global inter-op pool once.
                pass
        self.model: YOLO = None
        self._inference_lock = threading.Lock()

        self._load_model()

    def _load_model(self) -> None:
        """
        Load YOLO model. If weights do not exist locally in models/,
        Ultralytics will automatically download them.
        """
        model_path = MODELS_DIR / self.model_name
        logger.info(f"Initializing YOLO model: '{self.model_name}'...")
        
        try:
            # Check if model exists in models/ dir, else pass model name (downloads to current directory or cache)
            root_path = MODELS_DIR.parent / self.model_name
            target = str(model_path if model_path.exists() else root_path if root_path.exists() else self.model_name)
            self.model = YOLO(target)
            logger.info(
                "Model '%s' loaded successfully (input=%s, max_det=%s, threads=%s)",
                self.model_name,
                self.input_size,
                self.max_detections,
                self.cpu_threads,
            )
            logger.info(
                "Detection thresholds: conf=%.2f, iou=%.2f",
                self.confidence,
                self.iou,
            )
            warmup_started = time.perf_counter()
            warm_frame = np.zeros((self.input_size, self.input_size, 3), dtype=np.uint8)
            self.model.predict(
                source=[warm_frame] * 4,
                conf=self.confidence,
                iou=self.iou,
                imgsz=self.input_size,
                max_det=self.max_detections,
                device=None if self.device == "auto" else self.device,
                verbose=False,
            )
            logger.info(
                "Model predictor warmed in %.0f ms before accepting camera frames",
                (time.perf_counter() - warmup_started) * 1000,
            )
        except Exception as e:
            logger.error(f"Failed to load YOLO model '{self.model_name}': {e}", exc_info=True)
            raise e

    def predict(self, frame: Any, classes: list = None) -> Any:
        """
        Run model inference on a frame with specified class filters and thresholds.
        Returns detection results only (no track IDs).
        """
        with self._inference_lock:
            # OpenMP settings belong to the calling native worker as well.
            if ((self.device == 'cpu' or not torch.cuda.is_available())
                    and torch.get_num_threads() != self.cpu_threads):
                torch.set_num_threads(self.cpu_threads)
            result = self.model.predict(
                source=frame,
                conf=self.confidence,
                iou=self.iou,
                classes=classes,
                imgsz=self.input_size,
                max_det=self.max_detections,
                device=None if self.device == "auto" else self.device,
                verbose=False,
            )
            # Ultralytics resets CPU threads during first predictor setup.
            # Bound threads after setup as well, avoiding excessive CPU spin.
            if not torch.cuda.is_available() or self.device == "cpu":
                if torch.get_num_threads() != self.cpu_threads:
                    torch.set_num_threads(self.cpu_threads)
            return result

    def predict_batch(self, frames, classes=None):
        """Ordered results; one model call for a bounded list of images."""
        if not frames:
            return []
        if len(frames) > 4:
            raise ValueError('At most four camera frames per batch')
        return self.predict(frames, classes=classes)


    def track(self, frame: Any, classes: list = None) -> Any:
        """
        Run unified detect-and-track inference on a frame in a single YOLO forward pass.
        Returns results with persistent track IDs via ByteTrack.
        TrafficPipeline must use this instead of calling predict() + track() separately.
        """
        with self._inference_lock:
            return self.model.track(
                source=frame,
                conf=self.confidence,
                iou=self.iou,
                classes=classes,
                imgsz=self.input_size,
                max_det=self.max_detections,
                persist=True,
                tracker="bytetrack.yaml",
                device=None if self.device == "auto" else self.device,
                verbose=False,
            )
