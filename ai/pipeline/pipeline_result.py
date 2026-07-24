"""
PipelineResult data model representing structured frame processing outputs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np

from ai.detection.detection_types import Detection
from ai.analytics.analytics_exporter import LaneStatistics
from ai.signal.signal_types import PriorityResult, HardwareCommand
from ai.signal.signal_decision import SignalDecision


@dataclass
class PipelineResult:
    """
    Encapsulates all outputs generated during a single pipeline frame step.
    Prevents tuple-unpacking errors as the pipeline expands across modules.
    """
    has_frame: bool
    annotated_frame: Optional[np.ndarray] = None
    detections: List[Detection] = field(default_factory=list)
    lane_stats: Dict[str, LaneStatistics] = field(default_factory=dict)
    priority_result: Optional[PriorityResult] = None
    signal_decision: Optional[SignalDecision] = None
    hardware_command: Optional[HardwareCommand] = None
    remaining_green_sec: int = 0
    is_phase_change: bool = False
