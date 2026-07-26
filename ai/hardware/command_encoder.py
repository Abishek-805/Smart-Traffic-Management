"""
CommandEncoder formats HardwareCommand objects into JSON payloads and serial transmission packets.
"""

import json
from typing import Dict, Any
from ai.signal.signal_types import HardwareCommand
from ai.utils.logger import get_logger

logger = get_logger("CommandEncoder")


class CommandEncoder:
    """
    Encodes strongly-typed HardwareCommand objects into JSON and raw serial protocol packet strings.
    """

    @staticmethod
    def encode_json(cmd: HardwareCommand) -> str:
        """Encode HardwareCommand into JSON string packet."""
        if hasattr(cmd, "to_json"):
            return cmd.to_json()
        return json.dumps(cmd.to_dict() if hasattr(cmd, "to_dict") else str(cmd))

    @staticmethod
    def encode_serial(cmd: HardwareCommand) -> str:
        """
        Encode HardwareCommand into a compact serial packet string for microcontrollers:
        Example: "SET_SIGNAL:NORTH:GREEN:30:YELLOW:3:PHASE:1"
        """
        raw_lane = getattr(cmd, "green_lane", "NORTH")
        lane_val = raw_lane.value if hasattr(raw_lane, "value") else str(raw_lane)
        green_str = str(lane_val).split(".")[-1].upper()

        green_dur = getattr(cmd, "green_duration_sec", 10)
        yellow_dur = getattr(cmd, "yellow_duration_sec", 3)
        phase_id = getattr(cmd, "phase_id", 1)

        return f"SET_SIGNAL:{green_str}:GREEN:{green_dur}:YELLOW:{yellow_dur}:PHASE:{phase_id}"
