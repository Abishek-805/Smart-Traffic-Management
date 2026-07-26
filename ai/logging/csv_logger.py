"""
CSVLogger appends structured signal decision records to a CSV log file.
"""

import csv
from pathlib import Path
from typing import Dict, Any, Optional
from config.paths import DECISION_CSV_LOG_PATH
from ai.utils.logger import get_logger

logger = get_logger("CSVLogger")


class CSVLogger:
    """
    Appends signal phase decisions to a persistent CSV log file.
    """

    HEADERS = [
        "timestamp",
        "datetime_str",
        "phase_id",
        "selected_lane",
        "green_duration_sec",
        "yellow_duration_sec",
        "decision_reason",
        "reason_details",
        "total_vehicles",
        "priority_score",
        "pipeline_health",
    ]

    def __init__(self, log_path: Path = DECISION_CSV_LOG_PATH):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_header()

    def _ensure_header(self) -> None:
        """Create CSV file with column headers if missing."""
        if not self.log_path.exists() or self.log_path.stat().st_size == 0:
            try:
                with open(self.log_path, mode="w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(self.HEADERS)
                logger.info(f"Initialized CSV log file with headers: '{self.log_path}'")
            except Exception as e:
                logger.error(f"Failed to write CSV header: {e}")

    def log(self, entry: Dict[str, Any]) -> None:
        """
        Append a decision log record to the CSV file.
        """
        try:
            row = [
                entry.get("timestamp", 0.0),
                entry.get("datetime_str", ""),
                entry.get("phase_id", 0),
                entry.get("selected_lane", ""),
                entry.get("green_duration_sec", 0),
                entry.get("yellow_duration_sec", 0),
                entry.get("decision_reason", ""),
                entry.get("reason_details", ""),
                entry.get("total_vehicles", 0),
                entry.get("priority_score", 0.0),
                entry.get("pipeline_health", "INFO"),
            ]
            with open(self.log_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row)
        except Exception as e:
            logger.error(f"Error logging to CSV file '{self.log_path}': {e}")
