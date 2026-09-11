"""
Production-grade structured logger for multi-file log management.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from pathlib import Path
from typing import Optional

from config.paths import APP_LOG_PATH, DETECTION_LOG_PATH, ERROR_LOG_PATH


def _bounded_env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


def setup_loggers() -> logging.Logger:
    """
    Initialize and configure root, detection, and error loggers.
    """
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Base Application Logger
    app_logger = logging.getLogger("TrafficSystem")
    app_logger.setLevel(logging.INFO)

    if not app_logger.handlers:
        max_bytes = _bounded_env_int("TRAFFIC_LOG_MAX_BYTES", 5_000_000, 65_536, 100_000_000)
        backup_count = _bounded_env_int("TRAFFIC_LOG_BACKUP_COUNT", 3, 1, 20)
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        app_logger.addHandler(console_handler)

        # Main App File Handler
        file_handler = RotatingFileHandler(
            APP_LOG_PATH, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        app_logger.addHandler(file_handler)

        # Error File Handler
        error_handler = RotatingFileHandler(
            ERROR_LOG_PATH, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        app_logger.addHandler(error_handler)

    return app_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a named logger instance inheriting from TrafficSystem.
    """
    setup_loggers()
    if name:
        return logging.getLogger(f"TrafficSystem.{name}")
    return logging.getLogger("TrafficSystem")
