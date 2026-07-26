"""
ControlManager orchestrates post-decision operations: pre-transmission logging (CSV/JSONL/Console),
in-memory DecisionHistory tracking, non-blocking ESP32 hardware transmission, and dashboard rendering.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import numpy as np

from ai.pipeline.pipeline_result import PipelineResult
from ai.logging import DecisionLogger, DecisionHistory, DecisionLog
from ai.hardware import ESP32Interface, HardwareStatus
from dashboard.multi_camera_dashboard import MultiCameraDashboard
from ai.utils.logger import get_logger

logger = get_logger("ControlManager")


class ControlManager:
    """
    Control layer orchestrator separating perception/analytics pipeline execution
    from downstream logging, hardware communication, and dashboard UI rendering.
    """

    def __init__(
        self,
        esp32_port: Optional[str] = None,
        simulation_mode: bool = True,
        csv_log_path: Optional[Path] = None,
        json_log_path: Optional[Path] = None,
    ):
        self.decision_logger = DecisionLogger(
            csv_path=csv_log_path,
            json_path=json_log_path,
        )
        self.esp32_interface = ESP32Interface(
            port=esp32_port,
            simulation_mode=simulation_mode,
        )
        self.dashboard = MultiCameraDashboard(tile_width=640, tile_height=360)

        logger.info("ControlManager initialized (DecisionLogger, ESP32Interface, DecisionHistory, Dashboard UI)")

    def process_result(self, result: PipelineResult) -> np.ndarray:
        """
        Process a PipelineResult: handle phase change logging, non-blocking ESP32 command transmission,
        and render composite dashboard UI.

        Args:
            result: PipelineResult returned from TrafficPipeline.process_step().

        Returns:
            np.ndarray: Rendered composite dashboard image canvas.
        """
        if not result.has_frame:
            return self.dashboard.render_from_result(result)

        # 1. Handle new Phase Change decision event
        if result.is_phase_change and result.signal_decision and result.hardware_command:
            # Pre-transmission logging to CSV, JSONL, console, and memory history
            log_entry = self.decision_logger.log_decision(
                decision=result.signal_decision,
                hardware_command=result.hardware_command,
                intersection_state=result.intersection_state,
                health=result.health,
            )

            # Non-blocking transmission to ESP32 hardware/simulation interface
            self.esp32_interface.send_command(result.hardware_command)

        # 2. Query hardware status and decision history
        hw_status = self.esp32_interface.get_status()
        history_hud_lines = self.decision_logger.history.format_for_hud(limit=3)

        # 3. Render composite Control Dashboard
        dashboard_frame = self.dashboard.render_from_result(
            result=result,
            hardware_status=hw_status,
            decision_history=history_hud_lines,
        )

        return dashboard_frame

    def release(self) -> None:
        """Release hardware connections and logger resources."""
        logger.info("Shutting down ControlManager...")
        if self.esp32_interface:
            self.esp32_interface.close()
