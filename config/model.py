"""
YOLO model configuration parameters.
"""

# Model selection - default to latest YOLO11 Nano model
MODEL_NAME = "yolo11n.pt"

# Inference parameters
CONFIDENCE_THRESHOLD = 0.35
IOU_THRESHOLD = 0.45

# Execution device: "auto", "cpu", "cuda", or "mps"
DEVICE = "auto"
