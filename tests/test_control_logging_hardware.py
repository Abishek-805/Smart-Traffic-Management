"""
Unit test suite for Sprint 6 ControlManager, DecisionLogger, CSV/JSON Loggers, CommandEncoder, and ESP32Interface.
"""

import unittest
from pathlib import Path
import tempfile
import os
import json
import numpy as np
from types import SimpleNamespace
from unittest.mock import patch

from ai.signal import (
    SignalDecision,
    HardwareCommand,
    LaneName,
    DecisionReason,
)
from ai.logging import (
    DecisionLog,
    DecisionLogger,
    CSVLogger,
    JSONLogger,
    DecisionHistory,
)
from ai.hardware import (
    CommandEncoder,
    ESP32Interface,
    HardwareStatus,
)
from ai.controller import ControlManager
from ai.pipeline.pipeline_result import PipelineResult
from ai.pipeline.intersection_state import IntersectionState


class TestControlLoggingHardware(unittest.TestCase):
    """Test suite for Sprint 6 logging, hardware layer, and ControlManager."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.temp_dir.name) / "test_decisions.csv"
        self.json_path = Path(self.temp_dir.name) / "test_decisions.jsonl"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_command_encoder(self):
        """Test CommandEncoder serial and JSON formatting."""
        cmd = HardwareCommand(
            phase_id=1,
            green_lane=LaneName.NORTH,
            green_duration_sec=30,
            yellow_duration_sec=3,
            red_lanes=[LaneName.SOUTH, LaneName.EAST, LaneName.WEST],
            priority_score=15.5,
            reason=DecisionReason.NORMAL,
            reason_details="Highest PCE priority",
        )

        serial_str = CommandEncoder.encode_serial(cmd)
        self.assertIn("SET_SIGNAL:NORTH:GREEN:30:YELLOW:3:PHASE:1", serial_str)

        json_str = CommandEncoder.encode_json(cmd)
        self.assertIn("SIGNAL_PHASE", json_str)
        self.assertIn("North", json_str)

    def test_02_esp32_interface_simulation_mode(self):
        """Test ESP32Interface operating safely in simulation mode."""
        esp32 = ESP32Interface(simulation_mode=True)
        status = esp32.get_status()

        self.assertTrue(status.simulation_mode)
        self.assertFalse(status.connected)
        self.assertEqual(status.connection_state, "SIMULATION")

        cmd = HardwareCommand(
            phase_id=2,
            green_lane=LaneName.EAST,
            green_duration_sec=20,
            yellow_duration_sec=3,
            red_lanes=[LaneName.NORTH, LaneName.SOUTH, LaneName.WEST],
            priority_score=10.0,
            reason=DecisionReason.NORMAL,
            reason_details="Fairness bonus",
        )

        success = esp32.send_command(cmd)
        self.assertTrue(success)
        self.assertEqual(esp32.get_status().total_commands_sent, 1)

        esp32.close()

    @staticmethod
    def _hardware_command():
        return HardwareCommand(
            phase_id=3,
            green_lane=LaneName.SOUTH,
            green_duration_sec=15,
            yellow_duration_sec=3,
            red_lanes=[LaneName.NORTH, LaneName.EAST, LaneName.WEST],
            priority_score=9.0,
            reason=DecisionReason.NORMAL,
            reason_details="Hardware lifecycle test",
        )

    def test_esp32_hardware_mode_uses_configured_port_and_records_ack(self):
        class FakeConnection:
            is_open = True

            def __init__(self):
                self.writes = []

            def write(self, value):
                self.writes.append(value)

            def flush(self):
                return None

            def readline(self):
                return b"ACK:PHASE:3\n"

            def close(self):
                self.is_open = False

        connection = FakeConnection()
        serial_module = SimpleNamespace(Serial=lambda port, baudrate, timeout: connection)

        with patch("ai.hardware.esp32_interface.serial", serial_module), patch("ai.hardware.esp32_interface.time.sleep"):
            interface = ESP32Interface(port="TEST_PORT", baudrate=57600, simulation_mode=False)
            sent = interface.send_command(self._hardware_command())

        status = interface.get_status()
        self.assertTrue(sent)
        self.assertEqual(status.connection_state, "CONNECTED")
        self.assertEqual(status.port, "TEST_PORT")
        self.assertEqual(status.baudrate, 57600)
        self.assertEqual(status.last_ack, "ACK:PHASE:3")
        self.assertGreater(status.last_ack_time, 0)
        self.assertEqual(len(connection.writes), 1)

    def test_unavailable_requested_esp32_reports_error_not_simulation(self):
        def unavailable(*_args, **_kwargs):
            raise OSError("port unavailable")

        serial_module = SimpleNamespace(Serial=unavailable)
        with patch("ai.hardware.esp32_interface.serial", serial_module), patch("ai.hardware.esp32_interface.time.sleep"):
            interface = ESP32Interface(port="MISSING_PORT", simulation_mode=False)

        status = interface.get_status()
        self.assertFalse(status.simulation_mode)
        self.assertFalse(status.connected)
        self.assertEqual(status.connection_state, "ERROR")
        self.assertIn("port unavailable", status.last_error)
        self.assertFalse(interface.send_command(self._hardware_command()))

    def test_esp32_reconnect_recovers_after_initial_failure(self):
        class FakeConnection:
            is_open = True

            def close(self):
                self.is_open = False

        attempts = iter([OSError("first failure"), FakeConnection()])

        def open_serial(*_args, **_kwargs):
            result = next(attempts)
            if isinstance(result, Exception):
                raise result
            return result

        serial_module = SimpleNamespace(Serial=open_serial)
        with patch("ai.hardware.esp32_interface.serial", serial_module), patch("ai.hardware.esp32_interface.time.sleep"):
            interface = ESP32Interface(port="TEST_PORT", simulation_mode=False)
            recovered = interface.reconnect()

        self.assertTrue(recovered)
        self.assertEqual(interface.get_status().connection_state, "CONNECTED")

    def test_requested_hardware_error_is_not_safe_to_run(self):
        from ai.hardware.esp32_interface import hardware_is_safe_to_run

        status = HardwareStatus(simulation_mode=False, connection_state="ERROR")

        self.assertFalse(hardware_is_safe_to_run(status))

    def test_03_csv_and_json_loggers(self):
        """Test CSVLogger and JSONLogger file writing."""
        csv_logger = CSVLogger(log_path=self.csv_path)
        json_logger = JSONLogger(log_path=self.json_path)

        entry = {
            "timestamp": 1721890000.0,
            "datetime_str": "2026-07-25 10:00:00",
            "phase_id": 1,
            "selected_lane": "NORTH",
            "green_duration_sec": 30,
            "yellow_duration_sec": 3,
            "decision_reason": "NORMAL",
            "reason_details": "Highest score",
            "total_vehicles": 15,
            "priority_score": 25.4,
            "pipeline_health": "INFO",
        }

        csv_logger.log(entry)
        json_logger.log(entry)

        self.assertTrue(self.csv_path.exists())
        self.assertTrue(self.json_path.exists())

        # Verify CSV content
        with open(self.csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 2)  # Header + 1 row
            self.assertIn("NORTH", lines[1])

        # Verify JSONL content
        with open(self.json_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)
            parsed = json.loads(lines[0])
            self.assertEqual(parsed["selected_lane"], "NORTH")

    def test_04_decision_history(self):
        """Test DecisionHistory buffer and HUD formatting."""
        history = DecisionHistory(max_history=5)
        self.assertEqual(len(history.records), 0)

        log1 = DecisionLog(
            timestamp=1.0, datetime_str="t1", phase_id=1, selected_lane="NORTH",
            green_duration=30, yellow_duration=3, decision_reason="NORMAL",
            reason_details="", total_vehicles=10, priority_score=15.0
        )
        log2 = DecisionLog(
            timestamp=2.0, datetime_str="t2", phase_id=2, selected_lane="EAST",
            green_duration=20, yellow_duration=3, decision_reason="EMERGENCY",
            reason_details="", total_vehicles=5, priority_score=1000.0
        )

        history.add(log1)
        history.add(log2)

        self.assertEqual(len(history.records), 2)
        hud_lines = history.format_for_hud(limit=2)
        self.assertEqual(len(hud_lines), 2)
        self.assertIn("EAST", hud_lines[0])

    def test_05_control_manager_integration(self):
        """Test ControlManager processing PipelineResult objects."""
        control = ControlManager(
            simulation_mode=True,
            csv_log_path=self.csv_path,
            json_log_path=self.json_path,
        )

        cmd = HardwareCommand(
            phase_id=1, green_lane=LaneName.NORTH, green_duration_sec=30,
            yellow_duration_sec=3, red_lanes=[], priority_score=20.0,
            reason=DecisionReason.NORMAL, reason_details="Optimal"
        )
        decision = SignalDecision(
            phase_id=1, green_lane=LaneName.NORTH, green_duration_sec=30,
            yellow_duration_sec=3, priority_score=20.0, reason=DecisionReason.NORMAL,
            reason_details="Optimal"
        )

        result = PipelineResult(
            has_frame=True,
            is_phase_change=True,
            signal_decision=decision,
            hardware_command=cmd,
            intersection_state=IntersectionState(total_vehicles=12),
        )

        canvas = control.process_result(result)

        self.assertIsNotNone(canvas)
        self.assertIsInstance(canvas, np.ndarray)
        self.assertEqual(len(control.decision_logger.history.records), 1)

        control.release()

    def test_hardware_transmission_failure_pauses_runtime_and_forces_all_red(self):
        from core.application_context import ApplicationContext

        previous = ApplicationContext._instance
        ctx = ApplicationContext()
        ApplicationContext._instance = ctx
        control = ControlManager(simulation_mode=True, headless=True)
        cmd = self._hardware_command()
        decision = SignalDecision(
            phase_id=3, green_lane=LaneName.SOUTH, green_duration_sec=15,
            yellow_duration_sec=3, priority_score=9.0, reason=DecisionReason.NORMAL,
            reason_details="Hardware lifecycle test",
        )
        result = PipelineResult(
            has_frame=True, is_phase_change=True, signal_decision=decision,
            hardware_command=cmd, intersection_state=IntersectionState(total_vehicles=1),
            signal_state="GREEN",
        )
        try:
            with patch.object(control.esp32_interface, "send_command", return_value=False):
                control.process_result(result)
            self.assertFalse(ctx.system_running)
            self.assertEqual(result.signal_state, "ALL_RED")
        finally:
            control.release()
            ApplicationContext._instance = previous


if __name__ == "__main__":
    unittest.main()
