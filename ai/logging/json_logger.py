"""
JSONLogger appends structured signal decision records as JSON-Lines (.jsonl) entries.
"""

import json
from pathlib import Path
from typing import Dict, Any
from config.paths import DECISION_JSON_LOG_PATH
from ai.utils.logger import get_logger

logger = get_logger("JSONLogger")


class JSONLogger:
    """
    Appends signal phase decision records to a JSON-Lines file for audit logging and analysis.
    """

    def __init__(self, log_path: Path = DECISION_JSON_LOG_PATH):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, entry: Dict[str, Any]) -> None:
        """
        Append a decision record dictionary to the JSON-Lines log file.
        """
        try:
            line = json.dumps(entry, default=str)
            with open(self.log_path, mode="a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            logger.error(f"Error writing JSON-Lines log to '{self.log_path}': {e}")
