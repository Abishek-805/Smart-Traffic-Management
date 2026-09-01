"""
LogService handles retrieval and filtering of classified, structured log records.
Categories: INFO, WARNING, ERROR, AI, NODE, ESP32, SYSTEM.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid


class LogService:
    """
    Service layer providing categorized log stream queries and log exports.
    """

    def __init__(self):
        self._logs: List[Dict[str, Any]] = self._generate_initial_logs()

    def _generate_initial_logs(self) -> List[Dict[str, Any]]:
        """Pre-populate sample structured log entries."""
        return []

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
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
