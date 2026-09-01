"""
PipelineResult data model representing structured frame processing outputs across single and multi-camera pipelines.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np

from ai.detection.detection_types import Detection
from ai.analytics.analytics_exporter import LaneStatistics
from ai.signal.signal_types import PriorityResult, HardwareCommand
from ai.signal.signal_decision import SignalDecision
from ai.pipeline.pipeline_health import PipelineHealth
from ai.pipeline.intersection_state import LaneProcessingResult, IntersectionState


@dataclass
class PipelineResult:
    """
    Encapsulates all perception, analytics, decision, and diagnostic outputs
    generated during a single pipeline step execution.
    """
    has_frame: bool
    annotated_frame: Optional[np.ndarray] = None
    
    # Per-lane processing container map
    lane_results: Dict[str, LaneProcessingResult] = field(default_factory=dict)
    
    # Unified Intersection State
    intersection_state: Optional[IntersectionState] = None
    
    # Single-camera backward compatibility accessors
    detections: List[Detection] = field(default_factory=list)
    lane_stats: Dict[str, LaneStatistics] = field(default_factory=dict)
    multi_detections: Dict[str, List[Detection]] = field(default_factory=dict)
    multi_annotated_frames: Dict[str, np.ndarray] = field(default_factory=dict)

    # Signal Decision Engine outputs
    priority_result: Optional[PriorityResult] = None
    signal_decision: Optional[SignalDecision] = None
    hardware_command: Optional[HardwareCommand] = None
    health: Optional[PipelineHealth] = None
    remaining_green_sec: int = 0
    signal_state: str = "ALL_RED"
    is_phase_change: bool = False
    latency_metrics: Dict[str, float] = field(default_factory=dict)
    # Phase 3.5 — Scheduler stability tracking
    stability_metrics: Dict[str, Any] = field(default_factory=dict)
