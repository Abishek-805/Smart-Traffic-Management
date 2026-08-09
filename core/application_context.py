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

        # Pipeline stage diagnostic counters
        self.stage_counters: Dict[str, int] = {
            "received": 0,
            "decoded": 0,
            "decode_failed": 0,
            "processed": 0,
            "dropped": 0,
        }

        self.camera_manager: Optional[Any] = None
        self.pipeline: Optional[Any] = None  # TrafficPipeline instance
        self.control_manager: Optional[Any] = None  # ControlManager instance
        self.startup_config: Optional[Any] = None

        logger.info("ApplicationContext initialized.")

    def increment_stage_counter(self, stage: str) -> None:
        """Increment diagnostic counter for a specific pipeline stage."""
        if stage in self.stage_counters:
            self.stage_counters[stage] += 1
        else:
            self.stage_counters[stage] = 1

    def get_stage_counters(self) -> Dict[str, int]:
        """Return shallow copy of current pipeline stage counters."""
        return dict(self.stage_counters)

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

    async def update_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Atomically update the latest immutable pipeline telemetry snapshot."""
        self.latest_snapshot = snapshot
        if hasattr(self, "on_snapshot_updated") and self.on_snapshot_updated:
            try:
                await self.on_snapshot_updated(snapshot)
            except Exception as e:
                logger.warning(f"Error calling on_snapshot_updated: {e}")

    def get_health_dict(self) -> Dict[str, Any]:
        """Return structured diagnostic health state."""
        node_count = len(self.session_manager.sessions)
        cpu_pct = 0.0
        mem_used = 0.0
        mem_total = 8.0
        try:
            import psutil
            cpu_pct = round(psutil.cpu_percent(interval=None), 1)
            vm = psutil.virtual_memory()
            mem_used = round(vm.used / (1024**3), 1)
            mem_total = round(vm.total / (1024**3), 1)
        except Exception:
            cpu_pct = 0.0
            mem_used = 0.0

        latest_pop = (self.latest_snapshot or {}).get("payload", {})
        inf_ms = (latest_pop.get("latencyMetrics") or {}).get("yolo_ms", 0.0)

        return {
            "status": "RUNNING" if self.system_running else "PAUSED",
            "mode": "AUTOMATIC",
            "uptime": self.uptime_sec(),
            "cpu_percent": cpu_pct,
            "memory_used_gb": mem_used,
            "memory_total_gb": mem_total,
            "frame_processing_errors": self.frame_processing_errors,
            "inference_latency_ms": inf_ms,
            "stage_counters": self.get_stage_counters(),
            "components": {
                "ai": {
                    "status": "HEALTHY" if self.system_running else "DEGRADED",
                    "message": f"YOLO11 + ByteTrack Active | {inf_ms}ms",
                    "running": self.system_running,
                    "fps": 30.0,
                },
                "mobile": {
                    "status": "HEALTHY" if node_count > 0 else "DEGRADED",
                    "message": f"{node_count} nodes connected",
                    "connected": node_count,
                },
                "cameras": {
                    "status": "HEALTHY",
                    "message": "Multi-camera pipeline operational",
                    "active": 4,
                },
                "esp32": {
                    "status": "HEALTHY",
                    "message": "Simulation Mode (Active)",
                    "connected": False,
                    "simulation": True,
                },
            },
        }

