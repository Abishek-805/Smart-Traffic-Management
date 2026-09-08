"""
YOLO model configuration parameters.
"""

import os
from pathlib import Path

# Provisional laptop profile: faster on the local CPU and better coverage of
# the supplied traffic scene. Validate on labelled video before Pi deployment.
MODEL_NAME = os.getenv("YOLO_MODEL_NAME", "yolov8n.pt")

# Inference parameters
CONFIDENCE_THRESHOLD = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.08"))
IOU_THRESHOLD = float(os.getenv("YOLO_IOU", "0.60"))
INPUT_SIZE = max(320, min(1280, int(os.getenv("YOLO_INPUT_SIZE", "640"))))
MAX_DETECTIONS = max(10, min(1000, int(os.getenv("YOLO_MAX_DETECTIONS", "300"))))
CPU_THREADS = max(1, min(16, int(os.getenv("YOLO_CPU_THREADS", "4"))))
DETECTOR_FPS = max(0.1, min(30.0, float(os.getenv("DETECTOR_FPS", "2.0"))))

# ByteTrack receives detections down to the low threshold. Only detections at
# the high/new thresholds create tracks; lower-score boxes can recover an
# existing vehicle through short occlusions.
TRACK_HIGH_THRESHOLD = float(os.getenv("TRACK_HIGH_THRESHOLD", "0.15"))
TRACK_LOW_THRESHOLD = float(os.getenv("TRACK_LOW_THRESHOLD", "0.08"))
NEW_TRACK_THRESHOLD = float(os.getenv("NEW_TRACK_THRESHOLD", "0.15"))
TRACK_BUFFER_FRAMES = max(1, min(120, int(os.getenv("TRACK_BUFFER_FRAMES", "12"))))
TRACK_MATCH_THRESHOLD = float(os.getenv("TRACK_MATCH_THRESHOLD", "0.80"))

# Execution device: "auto", "cpu", "cuda", or "mps"
DEVICE = os.getenv("YOLO_DEVICE", "auto")


def _display_name(model_name: str) -> str:
    stem = Path(model_name).stem.lower().replace("_ncnn_model", "")
    for family in ("yolo26", "yolo11", "yolov8"):
        if family in stem:
            suffix = next((scale for scale in ("n", "s", "m", "l", "x")
                           if f"{family}{scale}" in stem), "")
            return f"{family.upper()}{suffix}"
    return Path(model_name).stem


MODEL_DISPLAY_NAME = os.getenv("YOLO_DISPLAY_NAME", _display_name(MODEL_NAME))
MODEL_RUNTIME = "NCNN" if "ncnn" in MODEL_NAME.lower() else "PyTorch"
