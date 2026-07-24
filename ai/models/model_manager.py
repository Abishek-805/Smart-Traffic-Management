"""
ModelManager handles vision model initialization, device selection, and abstraction over inference engines.
"""

from pathlib import Path
from typing import Any, Union, Dict
from ultralytics import YOLO

from config.model import MODEL_NAME, CONFIDENCE_THRESHOLD, IOU_THRESHOLD, DEVICE
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
    ):
        self.model_name = model_name
        self.confidence = confidence
        self.iou = iou
        self.device = device
        self.model: YOLO = None

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
            target = str(model_path) if model_path.exists() else self.model_name
            self.model = YOLO(target)
            logger.info(f"Model '{self.model_name}' loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load YOLO model '{self.model_name}': {e}", exc_info=True)
            raise e

    def predict(self, frame: Any, classes: list = None) -> Any:
        """
        Run model inference on a frame with specified class filters and thresholds.
        """
        return self.model.predict(
            source=frame,
            conf=self.confidence,
            iou=self.iou,
            classes=classes,
            device=None if self.device == "auto" else self.device,
            verbose=False,
        )
