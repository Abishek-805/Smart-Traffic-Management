"""
SignalDecision data model representing adaptive traffic light scheduling decisions.
This module is strictly independent of computer vision libraries (OpenCV, YOLO).
"""

from enum import Enum
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Union

from ai.signal.signal_types import LaneName, DecisionReason


@dataclass
class SignalDecision:
    """
    Immutable representation of an adaptive traffic signal phase decision.
    
    Attributes:
        green_lane (Union[LaneName, str]): The lane granted the green signal phase.
        green_duration_sec (int): Allocated duration of the green light phase in seconds.
        yellow_duration_sec (int): Duration of the transition yellow light phase in seconds.
        red_lanes (List[Union[LaneName, str]]): List of lanes holding red signals during this phase.
        priority_score (float): Computed priority score supporting this decision.
        reason (DecisionReason): Primary category for the decision (NORMAL, EMERGENCY, STARVATION).
        reason_details (str): Detailed human-readable explanation for why this decision was reached.
        timestamp (float): UNIX timestamp when the decision was generated.
    """
    green_lane: Union[LaneName, str]
    green_duration_sec: int
    yellow_duration_sec: int
    red_lanes: List[Union[LaneName, str]] = field(default_factory=list)
    priority_score: float = 0.0
    reason: DecisionReason = DecisionReason.NORMAL
    reason_details: str = "Standard Adaptive Priority"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize SignalDecision to a dictionary payload suitable for JSON export
        and hardware transmission (ESP32/MQTT).
        """
        green_str = self.green_lane.value if isinstance(self.green_lane, Enum) else str(self.green_lane)
        red_strs = [r.value if isinstance(r, Enum) else str(r) for r in self.red_lanes]
        reason_str = self.reason.value if isinstance(self.reason, Enum) else str(self.reason)

        return {
            "green_lane": green_str,
            "green_duration_sec": self.green_duration_sec,
            "yellow_duration_sec": self.yellow_duration_sec,
            "red_lanes": red_strs,
            "priority_score": round(self.priority_score, 2),
            "reason": reason_str,
            "reason_details": self.reason_details,
            "timestamp": round(self.timestamp, 3),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SignalDecision":
        """
        Instantiate a SignalDecision object from a dictionary payload.
        """
        green_raw = data.get("green_lane", "North")
        try:
            green_lane = LaneName(green_raw)
        except ValueError:
            green_lane = str(green_raw)

        red_raw = data.get("red_lanes", [])
        red_lanes = []
        for r in red_raw:
            try:
                red_lanes.append(LaneName(r))
            except ValueError:
                red_lanes.append(str(r))

        reason_raw = data.get("reason", "NORMAL")
        try:
            reason = DecisionReason(reason_raw)
        except ValueError:
            reason = DecisionReason.NORMAL

        return cls(
            green_lane=green_lane,
            green_duration_sec=int(data.get("green_duration_sec", 10)),
            yellow_duration_sec=int(data.get("yellow_duration_sec", 3)),
            red_lanes=red_lanes,
            priority_score=float(data.get("priority_score", 0.0)),
            reason=reason,
            reason_details=str(data.get("reason_details", data.get("decision_reason", "Imported Decision"))),
            timestamp=float(data.get("timestamp", time.time())),
        )

    def __str__(self) -> str:
        """
        Formatted human-readable string representation of the signal decision.
        """
        green_str = self.green_lane.value if isinstance(self.green_lane, Enum) else str(self.green_lane)
        red_strs = [r.value if isinstance(r, Enum) else str(r) for r in self.red_lanes]
        reds = ", ".join(red_strs) if red_strs else "None"
        reason_str = self.reason.value if isinstance(self.reason, Enum) else str(self.reason)
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))
        
        return (
            f"=================== SIGNAL DECISION ===================\n"
            f" Timestamp      : {time_str}\n"
            f" GREEN PHASE    : Lane '{green_str}' ({self.green_duration_sec}s)\n"
            f" YELLOW PHASE   : {self.yellow_duration_sec}s\n"
            f" RED PHASES     : [{reds}]\n"
            f" Priority Score : {self.priority_score:.2f}\n"
            f" Reason Category: [{reason_str}]\n"
            f" Reason Details : {self.reason_details}\n"
            f"======================================================="
        )
