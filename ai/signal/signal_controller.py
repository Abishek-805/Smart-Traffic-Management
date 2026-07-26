"""
SignalController prepares hardware-ready commands (ESP32/Serial/MQTT) from SignalDecision objects.
"""

from enum import Enum
from typing import Dict, Any, Optional
import json

from ai.signal.signal_types import LaneName, DecisionReason, HardwareCommand
from ai.signal.signal_decision import SignalDecision
from ai.utils.logger import get_logger

logger = get_logger("SignalController")


class SignalController:
    """
    Transforms SignalDecision objects into strongly-typed HardwareCommand payloads for Sprint 4 ESP32 integration.
    """

    def __init__(self):
        self.phase_counter = 0
        logger.info("SignalController initialized and ready for ESP32 hardware command generation.")

    def generate_command(self, decision: SignalDecision) -> HardwareCommand:
        """
        Generate a strongly-typed HardwareCommand payload from a SignalDecision.
        
        Args:
            decision (SignalDecision): Active signal phase decision.
            
        Returns:
            HardwareCommand: Strongly-typed hardware command dataclass object.
        """
        if not decision:
            raise ValueError("SignalDecision cannot be None when generating hardware command.")

        self.phase_counter += 1

        try:
            green_enum = LaneName(str(decision.green_lane).capitalize())
        except ValueError:
            green_enum = decision.green_lane

        red_enums = []
        for r in decision.red_lanes:
            try:
                red_enums.append(LaneName(str(r).capitalize()))
            except ValueError:
                red_enums.append(r)

        try:
            reason_enum = DecisionReason(decision.reason)
        except ValueError:
            reason_enum = DecisionReason.NORMAL

        cmd = HardwareCommand(
            phase_id=self.phase_counter,
            green_lane=green_enum,
            green_duration_sec=decision.green_duration_sec,
            yellow_duration_sec=decision.yellow_duration_sec,
            red_lanes=red_enums,
            priority_score=decision.priority_score,
            reason=reason_enum,
            reason_details=decision.reason_details,
            timestamp=decision.timestamp,
        )

        green_str = green_enum.value if isinstance(green_enum, Enum) else str(green_enum)
        reason_str = reason_enum.value if isinstance(reason_enum, Enum) else str(reason_enum)

        logger.info(
            f"[ESP32 Hardware Command #{self.phase_counter}] GREEN -> '{green_str}' "
            f"({decision.green_duration_sec}s) | Reason: {reason_str}"
        )

        return cmd

    def export_command_json(self, decision: SignalDecision) -> str:
        """
        Export hardware command as a formatted JSON string.
        """
        cmd = self.generate_command(decision)
        return cmd.to_json()
