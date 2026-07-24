"""
Enums and strongly-typed data structures for the adaptive traffic signal decision layer.
"""

from enum import Enum
from dataclasses import dataclass, field
import time
import json
from typing import Dict, List, Optional, Any


class LaneName(str, Enum):
    """
    Standard junction lane identifiers.
    Inherits from str to allow seamless JSON serialization.
    """
    NORTH = "North"
    SOUTH = "South"
    EAST = "East"
    WEST = "West"


class DecisionReason(str, Enum):
    """
    Structured categories for traffic signal phase allocations.
    Inherits from str to allow seamless JSON serialization.
    """
    NORMAL = "NORMAL"
    EMERGENCY = "EMERGENCY"
    STARVATION = "STARVATION"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"


@dataclass
class PriorityBreakdown:
    """
    Strongly-typed breakdown of score contributions.
    """
    pce: float
    queue: float
    congestion: float
    fairness_bonus: float = 0.0
    raw_pce: float = 0.0
    raw_queue_sec: float = 0.0
    raw_congestion_index: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "pce": round(self.pce, 2),
            "queue": round(self.queue, 2),
            "congestion": round(self.congestion, 2),
            "fairness_bonus": round(self.fairness_bonus, 2),
            "raw_pce": round(self.raw_pce, 2),
            "raw_queue_sec": round(self.raw_queue_sec, 2),
            "raw_congestion_index": round(self.raw_congestion_index, 2),
        }


@dataclass
class PriorityScore:
    """
    Strongly-typed representation of a lane's computed priority score and ranking.
    """
    lane: LaneName
    score: float
    rank: int
    breakdown: PriorityBreakdown

    def to_dict(self) -> Dict[str, Any]:
        lane_str = self.lane.value if isinstance(self.lane, Enum) else str(self.lane)
        return {
            "lane": lane_str,
            "score": round(self.score, 2),
            "rank": self.rank,
            "breakdown": self.breakdown.to_dict(),
        }


@dataclass
class PriorityResult:
    """
    Container holding sorted PriorityScore records, top priority lane, and calculation timestamp.
    """
    scores: List[PriorityScore]
    highest_priority: Optional[PriorityScore]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "highest_priority": self.highest_priority.to_dict() if self.highest_priority else None,
            "scores": [s.to_dict() for s in self.scores],
            "timestamp": round(self.timestamp, 3),
        }


@dataclass
class HardwareCommand:
    """
    Strongly-typed hardware command payload for Sprint 4 ESP32 integration.
    """
    phase_id: int
    green_lane: LaneName
    green_duration_sec: int
    yellow_duration_sec: int
    red_lanes: List[LaneName]
    priority_score: float
    reason: DecisionReason
    reason_details: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize HardwareCommand to dictionary payload."""
        green_str = self.green_lane.value if isinstance(self.green_lane, Enum) else str(self.green_lane)
        red_strs = [r.value if isinstance(r, Enum) else str(r) for r in self.red_lanes]
        reason_str = self.reason.value if isinstance(self.reason, Enum) else str(self.reason)

        return {
            "command": "SIGNAL_PHASE",
            "phase_id": self.phase_id,
            "green_lane": green_str,
            "green_time_sec": self.green_duration_sec,
            "yellow_time_sec": self.yellow_duration_sec,
            "red_lanes": red_strs,
            "priority_score": round(self.priority_score, 2),
            "reason": reason_str,
            "reason_details": self.reason_details,
            "timestamp": round(self.timestamp, 3),
        }

    def to_json(self) -> str:
        """Export HardwareCommand as a formatted JSON string."""
        return json.dumps(self.to_dict(), indent=2)
