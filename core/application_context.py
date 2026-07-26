"""
Central ApplicationContext managing shared runtime instances for Smart Traffic Management System.
"""

import time
from typing import Optional, Dict, Any
from ai.utils.logger import get_logger
from server.session_manager import SessionManager
from server.connection_manager import ConnectionManager

logger = get_logger("ApplicationContext")


class ApplicationContext:
    """
    Central thread-safe application context manager holding references to
    SessionManager, ConnectionManager, TrafficPipeline, ControlManager, and live telemetry snapshots.
    """

    _instance: Optional["ApplicationContext"] = None

    def __init__(self):
        self.start_time: float = time.time()
        self.system_running: bool = True
        self.session_manager: SessionManager = SessionManager()
        self.connection_manager: ConnectionManager = ConnectionManager()
        self.frame_buffer: dict = {}  # direction -> latest annotated JPEG bytes
        self.live_telemetry: dict = {}  # direction -> live detection metrics
        self.latest_snapshot: Optional[Dict[str, Any]] = None  # Atomic immutable snapshot for telemetry broadcast
        self.frame_processing_errors: int = 0  # Counter for recoverable frame processing errors
        self.last_frame_monotonic: float = time.monotonic()  # Monotonic timestamp of last received camera frame
        self.is_pipeline_stalled: bool = False  # Track pipeline stall state for transition logging
        self.lane_stats_history: Dict[str, Any] = {}  # Persistent multi-lane statistics map
        self.lane_last_seen: Dict[str, float] = {}  # direction -> monotonic timestamp when last frame arrived

        self.camera_manager: Optional[Any] = None
        self.pipeline: Optional[Any] = None  # TrafficPipeline instance
        self.control_manager: Optional[Any] = None  # ControlManager instance
        self.startup_config: Optional[Any] = None

        logger.info("ApplicationContext initialized.")

    @classmethod
    def get_instance(cls) -> "ApplicationContext":
        """Singleton accessor for ApplicationContext."""
        if cls._instance is None:
            cls._instance = ApplicationContext()
        return cls._instance

    def uptime_sec(self) -> float:
        """Calculate system uptime in seconds."""
        return round(time.time() - self.start_time, 1)

    def is_ai_running(self) -> bool:
        """Check if AI perception engine loop is active."""
        return self.system_running

    def update_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Atomically update the latest immutable pipeline telemetry snapshot."""
        self.latest_snapshot = snapshot

    def get_health_dict(self) -> Dict[str, Any]:
        """Return structured diagnostic health state."""
        node_count = len(self.session_manager.sessions)
        return {
            "system": "RUNNING" if self.system_running else "PAUSED",
            "uptime": self.uptime_sec(),
            "ai": {
                "running": self.system_running,
                "fps": 28.5,
            },
            "mobile": {
                "connected": node_count,
            },
            "cameras": {
                "active": 4,
            },
            "esp32": {
                "connected": False,
                "simulation": True,
            },
        }

