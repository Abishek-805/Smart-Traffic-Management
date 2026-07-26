"""
DecisionHistory maintains a fixed-size in-memory ring buffer of recent signal phase decisions.
"""

from collections import deque
from typing import List, Dict, Any, Optional
from ai.utils.logger import get_logger

logger = get_logger("DecisionHistory")


class DecisionHistory:
    """
    In-memory history buffer storing recent signal phase allocations for HUD rendering and analysis.
    """

    def __init__(self, max_history: int = 10):
        self.records: deque = deque(maxlen=max_history)

    def add(self, log_entry: Any) -> None:
        """Add a new decision record to history."""
        self.records.appendleft(log_entry)

    def get_recent(self, limit: int = 5) -> List[Any]:
        """Retrieve recent N decision log records."""
        return list(self.records)[:limit]

    def format_for_hud(self, limit: int = 3) -> List[str]:
        """
        Format recent decisions into compact HUD display lines:
        Example: ["Phase #12: NORTH (30s) - NORMAL", "Phase #11: EAST (18s) - STARVATION"]
        """
        lines = []
        for entry in self.get_recent(limit=limit):
            phase = getattr(entry, "phase_id", 0)
            lane = str(getattr(entry, "selected_lane", "NORTH")).upper()
            dur = getattr(entry, "green_duration", 0)
            reason = str(getattr(entry, "decision_reason", "NORMAL"))
            lines.append(f"Phase #{phase}: {lane} ({dur}s) — {reason}")
        return lines
