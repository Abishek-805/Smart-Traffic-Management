"""
SystemService provides system loop lifecycle management, diagnostic health metrics, and telemetry updates.
"""

from typing import Dict, Any
from core.application_context import ApplicationContext
from ai.utils.logger import get_logger
from config.model import MODEL_DISPLAY_NAME, MODEL_RUNTIME

logger = get_logger("SystemService")


class SystemService:
    """
    Service layer handling system start/stop/restart actions and health diagnostics.
    """

    def __init__(self, ctx: ApplicationContext = None):
        self.ctx = ctx or ApplicationContext.get_instance()

    def get_health(self) -> Dict[str, Any]:
        """Return structured diagnostic health dictionary."""
        return self.ctx.get_health_dict()

    def get_status(self) -> Dict[str, Any]:
        """Return detailed operational telemetry status dynamically from ApplicationContext latest snapshot."""
        snapshot = self.ctx.latest_snapshot or {}
        payload = snapshot.get("payload", {})
        hardware = payload.get("hardwareStatus") or {}
        if not hardware:
            hardware = self.ctx.get_health_dict().get("components", {}).get("esp32", {})
        return {
            "ai_engine": f"{MODEL_DISPLAY_NAME} {MODEL_RUNTIME} + ByteTrack",
            "running": self.ctx.system_running,
            "active_phase": payload.get("activePhase", "None"),
            "green_duration": payload.get("greenDuration", 0),
            "time_remaining": payload.get("timeRemaining", 0),
            "pce_queue": payload.get("pceScore", 0.0),
            "total_vehicles": payload.get("totalVehicles", 0),
            "detected_vehicles": payload.get("detectedVehicles", 0),
            "assigned_vehicles": payload.get("assignedVehicles", 0),
            "frame_processing_errors": self.ctx.frame_processing_errors,
            "esp32_mode": hardware.get("connection_state", "DISCONNECTED"),
            "nodes_connected": len(self.ctx.remote_nodes) if self.ctx.remote_runtime else sum(not s.is_expired() for s in self.ctx.session_manager.sessions.values()),
            # Phase 3.5: Scheduler stability telemetry
            "stability_metrics": payload.get("stabilityMetrics", {}),
        }

    def start_system(self) -> bool:
        """Start AI perception loop."""
        self.ctx.system_running = True
        logger.info("SystemService: Started AI system loop.")
        return True

    def stop_system(self) -> bool:
        """Stop AI perception loop."""
        self.ctx.system_running = False
        logger.info("SystemService: Stopped AI system loop.")
        return True

    def restart_system(self) -> bool:
        """Restart AI perception loop."""
        self.ctx.system_running = True
        logger.info("SystemService: Restarted AI system loop.")
        return True
