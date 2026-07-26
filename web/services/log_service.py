"""
LogService handles retrieval and filtering of classified, structured log records.
Categories: INFO, WARNING, ERROR, AI, NODE, ESP32, SYSTEM.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid


class LogService:
    """
    Service layer providing categorized log stream queries and log exports.
    """

    def __init__(self):
        self._logs: List[Dict[str, Any]] = self._generate_initial_logs()

    def _generate_initial_logs(self) -> List[Dict[str, Any]]:
        """Pre-populate sample structured log entries."""
        now = datetime.utcnow()
        return [
            {
                "id": str(uuid.uuid4()),
                "timestamp": (now - timedelta(seconds=10)).isoformat() + "Z",
                "level": "INFO",
                "category": "SYSTEM",
                "component": "ControlCenterApp",
                "message": "FastAPI Web Application initialized successfully.",
                "metadata": {"port": 8000, "protocol": "HTTP/1.1"},
            },
            {
                "id": str(uuid.uuid4()),
                "timestamp": (now - timedelta(seconds=8)).isoformat() + "Z",
                "level": "INFO",
                "category": "AI",
                "component": "YOLO11Detector",
                "message": "Model weights loaded successfully (yolo11n.pt). Inference device set to CPU.",
                "metadata": {"model": "yolo11n.pt", "framework": "PyTorch"},
            },
            {
                "id": str(uuid.uuid4()),
                "timestamp": (now - timedelta(seconds=6)).isoformat() + "Z",
                "level": "INFO",
                "category": "ESP32",
                "component": "ESP32Interface",
                "message": "Connected to ESP32 Signal Controller hardware on COM3 @ 115200 baud.",
                "metadata": {"port": "COM3", "baud": 115200},
            },
            {
                "id": str(uuid.uuid4()),
                "timestamp": (now - timedelta(seconds=4)).isoformat() + "Z",
                "level": "INFO",
                "category": "NODE",
                "component": "ConnectionManager",
                "message": "Mobile Camera Node paired: CAM-LANE1-9F8A (North Intersection).",
                "metadata": {"node_id": "CAM-LANE1-9F8A", "lane": "North"},
            },
            {
                "id": str(uuid.uuid4()),
                "timestamp": (now - timedelta(seconds=2)).isoformat() + "Z",
                "level": "WARNING",
                "category": "AI",
                "component": "FairnessManager",
                "message": "South direction queue length exceeded threshold (14.2m). Triggering priority shift.",
                "metadata": {"lane": "South", "queueLength": 14.2},
            },
            {
                "id": str(uuid.uuid4()),
                "timestamp": now.isoformat() + "Z",
                "level": "INFO",
                "category": "SYSTEM",
                "component": "SignalScheduler",
                "message": "Green phase allocated: North approach (25s duration).",
                "metadata": {"activePhase": "North", "duration": 25},
            },
        ]

    def add_log(
        self,
        level: str,
        category: str,
        component: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record a structured log entry."""
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level.upper(),
            "category": category.upper(),
            "component": component,
            "message": message,
            "metadata": metadata or {},
        }
        self._logs.insert(0, entry)
        if len(self._logs) > 500:
            self._logs.pop()
        return entry

    def get_logs(
        self,
        category: Optional[str] = None,
        level: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Filter log records by category, level, or search keyword."""
        results = self._logs
        if category and category.upper() != "ALL":
            results = [l for l in results if l["category"] == category.upper()]
        if level and level.upper() != "ALL":
            results = [l for l in results if l["level"] == level.upper()]
        if search:
            q = search.lower()
            results = [
                l for l in results
                if q in l["message"].lower() or q in l["component"].lower() or q in l["category"].lower()
            ]
        return results[:limit]
