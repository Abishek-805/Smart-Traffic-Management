"""
Unit tests for SignalController hardware command generator.
"""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from ai.signal import (
    LaneName,
    DecisionReason,
    SignalDecision,
    SignalController,
    HardwareCommand,
)


def test_signal_controller():
    print("=== Running SignalController Unit Test ===")

    controller = SignalController()

    decision = SignalDecision(
        green_lane=LaneName.NORTH,
        green_duration_sec=35,
        yellow_duration_sec=3,
        red_lanes=[LaneName.SOUTH, LaneName.EAST, LaneName.WEST],
        priority_score=22.25,
        reason=DecisionReason.NORMAL,
        reason_details="Highest weighted priority score.",
    )

    cmd = controller.generate_command(decision)
    assert isinstance(cmd, HardwareCommand)
    assert cmd.phase_id == 1
    assert cmd.green_lane == LaneName.NORTH
    assert cmd.green_duration_sec == 35
    assert cmd.yellow_duration_sec == 3
    assert cmd.priority_score == 22.25
    assert cmd.reason == DecisionReason.NORMAL

    dict_payload = cmd.to_dict()
    assert dict_payload["command"] == "SIGNAL_PHASE"
    assert dict_payload["green_lane"] == "North"
    assert dict_payload["red_lanes"] == ["South", "East", "West"]

    json_str = cmd.to_json()
    assert '"command": "SIGNAL_PHASE"' in json_str
    assert '"green_lane": "North"' in json_str

    print("✔ SignalController HardwareCommand dataclass test passed successfully!")


if __name__ == "__main__":
    test_signal_controller()
