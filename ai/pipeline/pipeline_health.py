"""
PipelineHealth data model and diagnostic evaluation engine.
Centralizes pipeline sanity checks, error severity classification, and health status reports.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

from ai.detection.detection_types import Detection
from ai.analytics.analytics_exporter import LaneStatistics
from ai.signal.signal_types import PriorityResult, HardwareCommand
from ai.signal.signal_decision import SignalDecision


class HealthSeverity(str, Enum):
    """
    Diagnostic alert severity levels.
    """
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class PipelineHealth:
    """
    Strongly-typed diagnostic snapshot of pipeline health across Perception, Analytics, and Decision stages.
    """
    detection_count: int
    tracked_count: int
    mapped_count: int
    analytics_ok: bool
    decision_active: bool
    phase_id: int
    remaining_time_sec: int
    warnings: List[str] = field(default_factory=list)
    severity: HealthSeverity = HealthSeverity.INFO

    @classmethod
    def evaluate(
        cls,
        raw_detections: List[Detection],
        tracked_detections: List[Detection],
        lane_stats: Dict[str, LaneStatistics],
        priority_result: Optional[PriorityResult],
        decision: Optional[SignalDecision],
        hardware_cmd: Optional[HardwareCommand],
        phase_id: int,
        remaining_time_sec: int,
    ) -> "PipelineHealth":
        """
        Evaluate runtime health across all pipeline stages and detect anomalies.
        
        Validation Rules:
        1. detections > 0 but tracks == 0 -> Tracking Failure (ERROR)
        2. tracks > 0 but mapped == 0 -> Lane Assignment Warning (WARNING)
        3. mapped > 0 but lane_stats == 0 -> Analytics Aggregation Warning (WARNING)
        4. priority exists but no decision -> Scheduler Failure (ERROR)
        5. decision exists but no hardware_cmd -> Controller Failure (ERROR)
        """
        det_cnt = len(raw_detections)
        track_cnt = len(tracked_detections)
        mapped_cnt = sum(s.live_count for s in lane_stats.values()) if lane_stats else 0
        analytics_ok = bool(lane_stats and len(lane_stats) > 0)
        decision_active = bool(decision is not None)

        warnings = []
        severity = HealthSeverity.INFO

        # Consistency Rule 1: Detections exist but tracking produces zero tracks
        if det_cnt > 0 and track_cnt == 0:
            warnings.append(f"Tracking Failure: {det_cnt} detections exist but 0 tracked")
            severity = HealthSeverity.ERROR

        # Consistency Rule 2: Tracked vehicles exist but zero mapped to lanes
        if track_cnt > 0 and mapped_cnt == 0:
            warnings.append(f"Lane Mapping Warning: {track_cnt} tracks outside lane ROIs")
            if severity != HealthSeverity.ERROR:
                severity = HealthSeverity.WARNING

        # Consistency Rule 3: Mapped count exists but analytics aggregation is empty
        if mapped_cnt > 0 and not analytics_ok:
            warnings.append("Analytics Warning: Lane statistics empty despite mapped vehicles")
            if severity != HealthSeverity.ERROR:
                severity = HealthSeverity.WARNING

        # Consistency Rule 4: Priority result computed but decision is None
        if priority_result is not None and decision is None:
            warnings.append("Scheduler Failure: Priority computed but decision is None")
            severity = HealthSeverity.ERROR

        # Consistency Rule 5: Signal decision exists but hardware command generation failed
        if decision is not None and hardware_cmd is None:
            warnings.append("Controller Failure: Decision exists but hardware command is None")
            severity = HealthSeverity.ERROR

        return cls(
            detection_count=det_cnt,
            tracked_count=track_cnt,
            mapped_count=mapped_cnt,
            analytics_ok=analytics_ok,
            decision_active=decision_active,
            phase_id=phase_id,
            remaining_time_sec=remaining_time_sec,
            warnings=warnings,
            severity=severity,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize health snapshot to dictionary."""
        return {
            "severity": self.severity.value,
            "detection_count": self.detection_count,
            "tracked_count": self.tracked_count,
            "mapped_count": self.mapped_count,
            "analytics_ok": self.analytics_ok,
            "decision_active": self.decision_active,
            "phase_id": self.phase_id,
            "remaining_time_sec": self.remaining_time_sec,
            "warnings": self.warnings,
        }
