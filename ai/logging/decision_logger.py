"""
DecisionLogger orchestrates phase decision logging across CSV files, JSON-Lines audits,
console logs, and in-memory DecisionHistory tracking.
"""

from dataclasses import dataclass, field
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from config.paths import DECISION_CSV_LOG_PATH, DECISION_JSON_LOG_PATH
from ai.logging.csv_logger import CSVLogger
from ai.logging.json_logger import JSONLogger
from ai.logging.decision_history import DecisionHistory
from ai.utils.logger import get_logger

logger = get_logger("DecisionLogger")


@dataclass
class DecisionLog:
    """
    Strongly-typed data container representing a logged signal phase decision.
    """
    timestamp: float
    datetime_str: str
    phase_id: int
    selected_lane: str
    green_duration: int
    yellow_duration: int
    decision_reason: str
    reason_details: str
    total_vehicles: int
    priority_score: float
    pipeline_health: str = "INFO"
    camera_health_summary: str = "All Connected"
    hardware_command_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary for JSON/CSV writers."""
        return {
            "timestamp": round(self.timestamp, 3),
            "datetime_str": self.datetime_str,
            "phase_id": self.phase_id,
            "selected_lane": self.selected_lane,
            "green_duration_sec": self.green_duration,
            "yellow_duration_sec": self.yellow_duration,
            "decision_reason": self.decision_reason,
            "reason_details": self.reason_details,
            "total_vehicles": self.total_vehicles,
            "priority_score": round(self.priority_score, 2),
            "pipeline_health": self.pipeline_health,
            "camera_health_summary": self.camera_health_summary,
            "hardware_command_json": self.hardware_command_json,
        }


class DecisionLogger:
    """
    Centralized decision logger interface coordinating CSV, JSON-Lines, console, and in-memory history.
    """

    def __init__(
        self,
        csv_path: Optional[Path] = None,
        json_path: Optional[Path] = None,
        history_size: int = 10,
    ):
        csv_target = csv_path if csv_path is not None else DECISION_CSV_LOG_PATH
        json_target = json_path if json_path is not None else DECISION_JSON_LOG_PATH

        self.csv_logger = CSVLogger(log_path=csv_target)
        self.json_logger = JSONLogger(log_path=json_target)
        self.history = DecisionHistory(max_history=history_size)

    def log_decision(
        self,
        decision: Any,
        hardware_command: Any,
        intersection_state: Optional[Any] = None,
        health: Optional[Any] = None,
    ) -> DecisionLog:
        """
        Record a signal phase allocation decision to CSV, JSONL, console, and memory history.

        Args:
            decision: Active SignalDecision object.
            hardware_command: Active HardwareCommand payload.
            intersection_state: Optional IntersectionState telemetry object.
            health: Optional PipelineHealth object.

        Returns:
            DecisionLog: Strongly-typed log record object.
        """
        now = time.time()
        datetime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))

        phase_id = getattr(decision, "phase_id", 1)
        raw_lane = getattr(decision, "green_lane", "NORTH")
        lane_val = raw_lane.value if hasattr(raw_lane, "value") else str(raw_lane)
        selected_lane = str(lane_val).split(".")[-1].upper()

        green_duration = getattr(decision, "green_duration_sec", 10)
        yellow_duration = getattr(decision, "yellow_duration_sec", 3)

        raw_reason = getattr(decision, "reason", "NORMAL")
        reason_val = raw_reason.value if hasattr(raw_reason, "value") else str(raw_reason)
        reason = str(reason_val).split(".")[-1].upper()
        reason_details = getattr(decision, "reason_details", "Optimal PCE priority")
        priority_score = getattr(decision, "priority_score", 0.0)

        total_vehicles = getattr(intersection_state, "total_vehicles", 0) if intersection_state else 0
        health_sev = str(getattr(health, "severity", "INFO")).replace("HealthSeverity.", "") if health else "INFO"

        hw_json = hardware_command.to_json() if hasattr(hardware_command, "to_json") else str(hardware_command)

        log_entry = DecisionLog(
            timestamp=now,
            datetime_str=datetime_str,
            phase_id=phase_id,
            selected_lane=selected_lane,
            green_duration=green_duration,
            yellow_duration=yellow_duration,
            decision_reason=reason,
            reason_details=reason_details,
            total_vehicles=total_vehicles,
            priority_score=priority_score,
            pipeline_health=health_sev,
            hardware_command_json=hw_json,
        )

        # 1. Console Log
        logger.info(
            f"📝 [DECISION LOGGED #Phase {phase_id}] Lane: '{selected_lane}' ({green_duration}s Green) | "
            f"Reason: {reason} | Score: {priority_score:.2f} | Vehicles: {total_vehicles}"
        )

        # 2. File Writers & History Buffer
        payload_dict = log_entry.to_dict()
        self.csv_logger.log(payload_dict)
        self.json_logger.log(payload_dict)
        self.history.add(log_entry)

        return log_entry
