"""
ByteTracker implementation utilizing Ultralytics persistent tracking integration.
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
    ByteTrack implementation that leverages Ultralytics YOLO persistent tracking pipeline.
    Assigns unique persistent track_id values to Detection dataclass objects.
    """

    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager or ModelManager()
        self.target_class_ids = list(TARGET_CLASS_IDS)
        logger.info("ByteTracker initialized using Ultralytics ByteTrack algorithm.")

    def update(
        self,
        detections: List[Detection],
        frame: Optional[np.ndarray] = None,
        frame_number: int = 0,
        timestamp: float = 0.0,
    ) -> List[Detection]:
        """
        Update vehicle tracks and assign persistent track_ids to detections.
        """
        if frame is None or len(detections) == 0:
            return detections

        try:
            # Run Ultralytics tracker on frame with ByteTrack
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
                    track_ids = boxes.id.int().cpu().tolist()
                    xyxy_tracked = boxes.xyxy.cpu().numpy().astype(int)
                    cls_tracked = boxes.cls.int().cpu().tolist()
                    conf_tracked = boxes.conf.cpu().numpy().tolist()

                    tracked_detections: List[Detection] = []

                    for i, tid in enumerate(track_ids):
                        cls_id = cls_tracked[i]
                        class_name = VEHICLE_CLASSES.get(cls_id, "vehicle")
                        bbox = (
                            int(xyxy_tracked[i][0]),
                            int(xyxy_tracked[i][1]),
                            int(xyxy_tracked[i][2]),
                            int(xyxy_tracked[i][3]),
                        )
                        conf = float(conf_tracked[i])

                        det = Detection(
                            class_name=class_name,
                            class_id=cls_id,
                            confidence=conf,
                            bbox=bbox,
                            track_id=tid,
                            frame_number=frame_number,
                            timestamp=timestamp,
                        )
                        tracked_detections.append(det)

                    return tracked_detections

        except Exception as e:
            logger.warning(f"Tracker error: {e}. Falling back to detection frame objects.", exc_info=False)

        return detections
