"""
YOLO model configuration parameters.
"""

import os
from pathlib import Path

# Stable laptop baseline. Raspberry Pi deployments should point this at an
# exported NCNN directory after running scripts/export_edge_model.py.
MODEL_NAME = os.getenv("YOLO_MODEL_NAME", "yolo26n.pt")

# Inference parameters
CONFIDENCE_THRESHOLD = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.35"))
IOU_THRESHOLD = float(os.getenv("YOLO_IOU", "0.45"))
INPUT_SIZE = max(320, min(1280, int(os.getenv("YOLO_INPUT_SIZE", "640"))))
MAX_DETECTIONS = max(10, min(1000, int(os.getenv("YOLO_MAX_DETECTIONS", "100"))))
CPU_THREADS = max(1, min(16, int(os.getenv("YOLO_CPU_THREADS", "4"))))

# Execution device: "auto", "cpu", "cuda", or "mps"
DEVICE = os.getenv("YOLO_DEVICE", "auto")


def _display_name(model_name: str) -> str:
    stem = Path(model_name).stem.lower().replace("_ncnn_model", "")
    for family in ("yolo26", "yolo11", "yolov8"):
        if family in stem:
            suffix = "n" if f"{family}n" in stem else ""
            return f"{family.upper()}{suffix}"
    return Path(model_name).stem


MODEL_DISPLAY_NAME = os.getenv("YOLO_DISPLAY_NAME", _display_name(MODEL_NAME))
MODEL_RUNTIME = "NCNN" if "ncnn" in MODEL_NAME.lower() else "PyTorch"
