"""Trustworthy per-frame stage timing based on the server monotonic clock."""

from dataclasses import dataclass, field
import math
import time
from typing import Optional


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


@dataclass
class FrameTiming:
    received_monotonic: float = field(default_factory=time.monotonic)
    received_wall_ms: Optional[float] = None
    capture_wall_ms: Optional[float] = None
    clock_skew_tolerance_ms: float = 2_000.0
    stages: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not _finite(self.received_monotonic):
            raise ValueError("received_monotonic must be finite")
        if self.received_wall_ms is None:
            self.received_wall_ms = time.time() * 1000.0
        self.stages.setdefault("received", float(self.received_monotonic))

    def mark(
        self,
        stage: str,
        monotonic: Optional[float] = None,
        wall_ms: Optional[float] = None,
    ) -> None:
        """Record a server stage; wall values are retained only as diagnostics."""
        value = time.monotonic() if monotonic is None else monotonic
        if not _finite(value):
            raise ValueError(f"{stage} monotonic timestamp must be finite")
        self.stages[stage] = float(value)
        if wall_ms is not None and _finite(wall_ms):
            self.stages[f"{stage}_wall_ms"] = float(wall_ms)

    def _duration(self, start: str, end: str) -> Optional[float]:
        start_value = self.stages.get(start)
        end_value = self.stages.get(end)
        if not _finite(start_value) or not _finite(end_value) or end_value < start_value:
            return None
        return round((end_value - start_value) * 1000.0, 3)

    def to_metrics(self, publication_monotonic: float) -> dict[str, Optional[float]]:
        if not _finite(publication_monotonic):
            raise ValueError("publication_monotonic must be finite")

        decoded = self.stages.get("decoded")
        selected = self.stages.get("selected")
        decode_start = "decode_start" if "decode_start" in self.stages else "received"
        if _finite(decoded) and _finite(selected) and decoded <= selected:
            coordinator_wait = self._duration("decoded", "selected")
        else:
            coordinator_wait = self._duration("received", "selected")

        inference_start = "inference_start" if "inference_start" in self.stages else "selected"
        total = self._duration_value(self.received_monotonic, publication_monotonic)
        arrival_age = None
        if _finite(self.capture_wall_ms) and _finite(self.received_wall_ms):
            candidate = float(self.received_wall_ms) - float(self.capture_wall_ms)
            if 0.0 <= candidate <= max(0.0, self.clock_skew_tolerance_ms):
                arrival_age = round(candidate, 3)

        return {
            "decode_ms": self._duration(decode_start, "decoded"),
            "coordinator_wait_ms": coordinator_wait,
            "inference_ms": self._duration(inference_start, "inference_end"),
            "tracking_ms": self._duration("inference_end", "tracking_end"),
            "analytics_ms": self._duration("tracking_end", "analytics_end"),
            "scheduler_ms": self._duration("analytics_end", "scheduler_end"),
            "publication_ms": self._duration("scheduler_end", "publication"),
            "server_total_ms": total,
            "arrival_age_ms": arrival_age,
            "frame_age_ms": total,
        }

    @staticmethod
    def _duration_value(start: float, end: float) -> Optional[float]:
        if not _finite(start) or not _finite(end) or end < start:
            return None
        return round((end - start) * 1000.0, 3)
