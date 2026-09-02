"""
Configuration package for Smart Traffic Management system.
"""

from config.paths import (
    ROOT_DIR,
    MODELS_DIR,
    VIDEOS_DIR,
    OUTPUTS_DIR,
    LOGS_DIR,
    DEFAULT_OUTPUT_PATH,
    APP_LOG_PATH,
    DETECTION_LOG_PATH,
    ERROR_LOG_PATH,
    get_timestamped_output_path,
)
from config.model import (
    MODEL_NAME,
    CONFIDENCE_THRESHOLD,
    IOU_THRESHOLD,
    DEVICE,
)
from config.ui import (
    WINDOW_NAME,
    CLASS_COLORS,
    DEFAULT_COLOR,
    BOX_THICKNESS,
    FONT_SCALE,
    FONT_THICKNESS,
    TEXT_COLOR,
    HUD_BG_COLOR,
    HUD_TEXT_COLOR,
)
from config.traffic import (
    TARGET_CLASS_NAMES,
)

__all__ = [
    "ROOT_DIR",
    "MODELS_DIR",
    "VIDEOS_DIR",
    "OUTPUTS_DIR",
    "LOGS_DIR",
    "DEFAULT_OUTPUT_PATH",
    "APP_LOG_PATH",
    "DETECTION_LOG_PATH",
    "ERROR_LOG_PATH",
    "get_timestamped_output_path",
    "MODEL_NAME",
    "CONFIDENCE_THRESHOLD",
    "IOU_THRESHOLD",
    "DEVICE",
    "WINDOW_NAME",
    "CLASS_COLORS",
    "DEFAULT_COLOR",
    "BOX_THICKNESS",
    "FONT_SCALE",
    "FONT_THICKNESS",
    "TEXT_COLOR",
    "HUD_BG_COLOR",
    "HUD_TEXT_COLOR",
    "TARGET_CLASS_NAMES",
]
