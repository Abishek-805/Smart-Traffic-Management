"""
Path configurations for data, models, logs, and outputs.
"""

from datetime import datetime
from pathlib import Path

# Root directory of the repository
ROOT_DIR = Path(__file__).resolve().parent.parent

# Core subdirectories
MODELS_DIR = ROOT_DIR / "models"
VIDEOS_DIR = ROOT_DIR / "videos"
OUTPUTS_DIR = ROOT_DIR / "outputs"
LOGS_DIR = ROOT_DIR / "logs"

# Ensure directories exist
for directory in [MODELS_DIR, VIDEOS_DIR, OUTPUTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# File paths
DEFAULT_VIDEO_PATH = VIDEOS_DIR / "traffic.mp4"
DEFAULT_OUTPUT_PATH = OUTPUTS_DIR / "detection.mp4"

# Log files
APP_LOG_PATH = LOGS_DIR / "application.log"
DETECTION_LOG_PATH = LOGS_DIR / "detection.log"
ERROR_LOG_PATH = LOGS_DIR / "errors.log"
DECISION_CSV_LOG_PATH = LOGS_DIR / "decisions.csv"
DECISION_JSON_LOG_PATH = LOGS_DIR / "decisions.jsonl"
# Config directory and runtime config profile
CONFIG_DIR = ROOT_DIR / "config"
RUNTIME_CONFIG_PATH = CONFIG_DIR / "runtime_config.json"


def get_timestamped_output_path(prefix: str = "detection") -> Path:
    """
    Generate a timestamped output video path.
    Example: outputs/detection_20260724_201500.mp4
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return OUTPUTS_DIR / f"{prefix}_{timestamp}.mp4"
