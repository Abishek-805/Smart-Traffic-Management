"""
VehicleDetector runs vehicle detection and produces structured Detection objects.
"""

import time
from typing import List, Tuple, Any
import numpy as np

from config.traffic import VEHICLE_CLASSES, TARGET_CLASS_IDS
from ai.models.model_manager import ModelManager
from ai.detection.detection_types import Detection
from ai.utils.logger import get_logger

logger = get_logger("VehicleDetector")


class VehicleDetector:
    """
    Detector responsible for extracting vehicle bounding boxes from frames.
    Decoupled from visual rendering.
    """

    def __init__(self, model_manager: ModelManager = None):
        self.model_manager = model_manager or ModelManager()
        self.target_class_ids = list(TARGET_CLASS_IDS)
        logger.info(f"VehicleDetector initialized focusing on classes: {VEHICLE_CLASSES}")

    def detect(self, frame: np.ndarray, frame_number: int = 0, timestamp: float = 0.0) -> Tuple[List[Detection], float]:
        """
        Detect vehicles in frame.
        
        Returns:
            Tuple[List[Detection], float]: List of detection objects and inference time in milliseconds.
        """
        start_time = time.perf_counter()
        
        # Perform inference restricted to vehicle class IDs
        results = self.model_manager.predict(frame, classes=self.target_class_ids)
        
        inference_time_ms = (time.perf_counter() - start_time) * 1000.0
        
        detections: List[Detection] = []
        
        if results and len(results) > 0:
            boxes = results[0].boxes
            if boxes is not None:
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    xyxy = box.xyxy[0].cpu().numpy().astype(int)
                    
                    class_name = VEHICLE_CLASSES.get(cls_id, "vehicle")
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
