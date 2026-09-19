"""Bounded, fair latest-frame handoff shared by every camera transport."""

from dataclasses import asdict, dataclass
from threading import RLock
from typing import Iterable, Optional


@dataclass
class FrameCounters:
    offered: int = 0
    selected: int = 0
    processed: int = 0
    replaced: int = 0
    stale_dropped: int = 0
    decode_failed: int = 0
    inference_failed: int = 0


class LatestFrameSlots:
    """Keep at most one pending frame per direction and select fairly."""

    def __init__(self, directions: Iterable[str], stale_after_sec: float = 2.5):
        normalized = tuple(dict.fromkeys(str(item).lower() for item in directions))
        if not normalized:
            raise ValueError("At least one camera direction is required")
        self._directions = normalized
        self._pending: dict[str, dict] = {}
        self._cursor = 0
        self._stale_after_sec = max(0.0, float(stale_after_sec))
        self._lock = RLock()
        self.counters = {direction: FrameCounters() for direction in normalized}

    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self._pending)

    def offer(self, direction: str, packet: dict) -> Optional[dict]:
        direction = str(direction).lower()
        with self._lock:
            if direction not in self.counters:
                raise ValueError(f"Unknown camera direction: {direction}")
            previous = self._pending.get(direction)
            self._pending[direction] = packet
            counter = self.counters[direction]
            counter.offered += 1
            if previous is not None:
                counter.replaced += 1
            return previous

    def select_due(self, now: float, max_items: int) -> list[dict]:
        if max_items <= 0:
            return []
        with self._lock:
            ordered = self._directions[self._cursor :] + self._directions[: self._cursor]
            selected: list[dict] = []
            last_direction = None
            for direction in ordered:
                packet = self._pending.get(direction)
                if packet is None:
                    continue
                received = packet.get("backend_receive_monotonic")
                if isinstance(received, (int, float)) and now - received > self._stale_after_sec:
                    self._pending.pop(direction, None)
                    self.counters[direction].stale_dropped += 1
                    continue
                if len(selected) >= max_items:
                    continue
                selected.append(self._pending.pop(direction))
                self.counters[direction].selected += 1
                last_direction = direction
            if last_direction is not None:
                self._cursor = (self._directions.index(last_direction) + 1) % len(self._directions)
            return selected

    def mark_processed(self, direction: str) -> None:
        with self._lock:
            self.counters[direction.lower()].processed += 1

    def mark_failure(self, direction: str, stage: str) -> None:
        with self._lock:
            counter = self.counters[direction.lower()]
            if stage == "decode":
                counter.decode_failed += 1
            elif stage == "inference":
                counter.inference_failed += 1
            else:
                raise ValueError(f"Unknown frame failure stage: {stage}")

    def mark_stale(self, direction: str) -> None:
        with self._lock:
            self.counters[direction.lower()].stale_dropped += 1

    def snapshot(self) -> dict[str, dict[str, int]]:
        with self._lock:
            return {direction: asdict(counter) for direction, counter in self.counters.items()}

    def clear(self) -> None:
        with self._lock:
            self._pending.clear()
