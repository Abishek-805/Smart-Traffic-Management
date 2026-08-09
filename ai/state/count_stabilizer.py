"""
CountStabilizer — Phase 3.5 Vehicle Count Stabilization.

Applies temporal smoothing to per-lane vehicle counts so the scheduler acts on
stable traffic patterns rather than single-frame noise.

Pipeline position:
    VehicleStateManager → AnalyticsExporter → CountStabilizer → PriorityCalculator → SignalScheduler

Features:
    - Per-lane rolling count history (last N frames)
    - Exponential Moving Average (EMA) smoothing with configurable alpha
    - Scheduler stability tracking (decision flip detection)
    - Scheduler input report logging for validation
"""

import copy
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Deque
from pathlib import Path

from ai.analytics.analytics_exporter import LaneStatistics
from config.traffic import EMA_ALPHA, COUNT_HISTORY_SIZE
from ai.utils.logger import get_logger

logger = get_logger("CountStabilizer")

# Path to scheduler input report log
_REPORT_PATH = Path("logs/scheduler_input_report.md")


@dataclass
class StabilityMetrics:
    """
    Tracks scheduler decision stability across frames.
    """
    total_decisions: int = 0
    stable_decisions: int = 0
    flipped_decisions: int = 0
    last_decision_lane: Optional[str] = None
    consecutive_stable_frames: int = 0
    max_raw_smoothed_delta: float = 0.0

    @property
    def stability_ratio(self) -> float:
        """Ratio of stable decisions to total decisions (1.0 = perfectly stable)."""
        if self.total_decisions == 0:
            return 1.0
        return round(self.stable_decisions / self.total_decisions, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_decisions": self.total_decisions,
            "stable_decisions": self.stable_decisions,
            "flipped_decisions": self.flipped_decisions,
            "last_decision_lane": self.last_decision_lane,
            "consecutive_stable_frames": self.consecutive_stable_frames,
            "stability_ratio": self.stability_ratio,
            "max_raw_smoothed_delta": round(self.max_raw_smoothed_delta, 2),
        }


class CountStabilizer:
    """
    Temporal smoothing layer between AnalyticsExporter and PriorityCalculator.

    Maintains per-lane rolling count histories and applies EMA smoothing to
    produce stable vehicle counts that prevent scheduler flicker from
    one-frame detection noise, temporary occlusions, or track ID switches.
    """

    def __init__(
        self,
        alpha: float = EMA_ALPHA,
        history_size: int = COUNT_HISTORY_SIZE,
    ):
        self.alpha = alpha
        self.history_size = history_size

        # Per-lane rolling count history (deque auto-trims to history_size)
        self._count_history: Dict[str, Deque[int]] = {
            "North": deque(maxlen=history_size),
            "South": deque(maxlen=history_size),
            "East": deque(maxlen=history_size),
            "West": deque(maxlen=history_size),
        }

        # Per-lane EMA state (persisted across frames)
        self._ema: Dict[str, float] = {
            "North": 0.0,
            "South": 0.0,
            "East": 0.0,
            "West": 0.0,
        }

        # Stability tracking
        self.metrics = StabilityMetrics()

        # Report log entries (written on flush)
        self._report_entries: List[Dict[str, Any]] = []

        logger.info(
            f"CountStabilizer initialized (EMA alpha={self.alpha}, "
            f"history_size={self.history_size})"
        )

    def stabilize(
        self,
        lane_stats: Dict[str, LaneStatistics],
        timestamp: Optional[float] = None,
    ) -> Dict[str, LaneStatistics]:
        """
        Apply EMA smoothing to per-lane vehicle counts.

        For each lane:
            1. Record raw live_count in rolling history
            2. Update EMA: smoothed = alpha * raw + (1 - alpha) * previous_ema
            3. Write smoothed_count into a copy of LaneStatistics
            4. Use smoothed_count as the effective live_count for scheduler input

        Args:
            lane_stats: Raw LaneStatistics from AnalyticsExporter.
            timestamp: Optional wall-clock timestamp for report logging.

        Returns:
            New Dict of LaneStatistics with smoothed counts applied.
        """
        ts = timestamp or time.time()
        stabilized: Dict[str, LaneStatistics] = {}

        for lane_name, stats in lane_stats.items():
            raw_count = stats.live_count

            # 1. Append raw count to rolling history
            history = self._count_history.get(lane_name)
            if history is None:
                history = deque(maxlen=self.history_size)
                self._count_history[lane_name] = history
            history.append(raw_count)

            # 2. EMA update
            prev_ema = self._ema.get(lane_name, 0.0)
            if len(history) == 1:
                # First frame: seed EMA with raw count
                new_ema = float(raw_count)
            else:
                new_ema = self.alpha * raw_count + (1.0 - self.alpha) * prev_ema
            self._ema[lane_name] = new_ema

            # 3. Build stabilized copy of LaneStatistics
            stabilized_stats = copy.copy(stats)
            stabilized_stats.smoothed_count = round(new_ema, 2)
            stabilized_stats.raw_count = raw_count

            # Override live_count with rounded smoothed value for scheduler consumption
            stabilized_stats.live_count = int(round(new_ema))

            # Recalculate PCE proportionally if count changed
            if raw_count > 0 and stabilized_stats.live_count != raw_count:
                scale = stabilized_stats.live_count / raw_count
                stabilized_stats.pce_score = round(stats.pce_score * scale, 2)

            stabilized[lane_name] = stabilized_stats

            # Track max delta for stability metrics
            delta = abs(raw_count - new_ema)
            self.metrics.max_raw_smoothed_delta = max(self.metrics.max_raw_smoothed_delta, delta)

        # 4. Log report entry
        self._log_report_entry(stabilized, ts)

        return stabilized

    def update_decision_stability(
        self,
        decision_lane: str,
        timestamp: float = 0.0,
    ) -> bool:
        """
        Track whether the scheduler decision is stable across frames.
        Called after SignalScheduler produces a decision.

        Returns:
            True if decision is stable (same as previous), False if it flipped.
        """
        self.metrics.total_decisions += 1

        if self.metrics.last_decision_lane == decision_lane:
            self.metrics.stable_decisions += 1
            self.metrics.consecutive_stable_frames += 1
            return True
        else:
            self.metrics.flipped_decisions += 1
            self.metrics.consecutive_stable_frames = 0
            self.metrics.last_decision_lane = decision_lane
            logger.info(
                f"[STABILITY] Decision flipped: → '{decision_lane}' "
                f"(total flips: {self.metrics.flipped_decisions})"
            )
            return False

    def get_count_history(self, lane_name: str) -> List[int]:
        """Return the rolling raw count history for a specific lane."""
        history = self._count_history.get(lane_name)
        return list(history) if history else []

    def get_ema(self, lane_name: str) -> float:
        """Return the current EMA value for a specific lane."""
        return self._ema.get(lane_name, 0.0)

    def get_stability_report(self) -> Dict[str, Any]:
        """
        Return a comprehensive stability report for diagnostics and dashboard.
        """
        report: Dict[str, Any] = {
            "metrics": self.metrics.to_dict(),
            "per_lane": {},
        }

        for lane_name in ["North", "South", "East", "West"]:
            history = self.get_count_history(lane_name)
            ema = self.get_ema(lane_name)
            report["per_lane"][lane_name] = {
                "raw_history": history,
                "ema": round(ema, 2),
                "history_mean": round(sum(history) / len(history), 2) if history else 0.0,
            }

        return report

    # ── Report Logging ────────────────────────────────────────────────────────

    def _log_report_entry(
        self,
        stabilized_stats: Dict[str, LaneStatistics],
        timestamp: float,
    ) -> None:
        """Accumulate a report entry for batch flushing."""
        entry: Dict[str, Any] = {"timestamp": timestamp, "lanes": {}}
        for lane_name, stats in stabilized_stats.items():
            entry["lanes"][lane_name] = {
                "raw_count": stats.raw_count,
                "smoothed_count": stats.smoothed_count,
                "difference": round(stats.raw_count - stats.smoothed_count, 2),
                "live_count": stats.live_count,
            }
        self._report_entries.append(entry)

    def flush_report(self) -> Optional[Path]:
        """
        Write accumulated report entries to logs/scheduler_input_report.md.
        Returns the path to the written file, or None if no entries.
        """
        if not self._report_entries:
            return None

        try:
            _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

            lines: List[str] = [
                "# Scheduler Input Report",
                "",
                f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**EMA Alpha:** {self.alpha}",
                f"**History Size:** {self.history_size}",
                f"**Total Entries:** {len(self._report_entries)}",
                "",
                "## Stability Metrics",
                "",
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Total Decisions | {self.metrics.total_decisions} |",
                f"| Stable Decisions | {self.metrics.stable_decisions} |",
                f"| Flipped Decisions | {self.metrics.flipped_decisions} |",
                f"| Stability Ratio | {self.metrics.stability_ratio:.2%} |",
                f"| Consecutive Stable Frames | {self.metrics.consecutive_stable_frames} |",
                f"| Max Raw-Smoothed Delta | {self.metrics.max_raw_smoothed_delta:.2f} |",
                "",
                "## Per-Frame Count Log",
                "",
                "| Timestamp | Lane | Raw Count | Smoothed Count | Difference | Decision |",
                "|-----------|------|-----------|----------------|------------|----------|",
            ]

            for entry in self._report_entries[-100:]:  # Keep last 100 entries
                ts_str = time.strftime('%H:%M:%S', time.localtime(entry["timestamp"]))
                for lane_name, lane_data in entry["lanes"].items():
                    lines.append(
                        f"| {ts_str} | {lane_name:<6} | {lane_data['raw_count']:<10} | "
                        f"{lane_data['smoothed_count']:<14.2f} | {lane_data['difference']:<10.2f} | "
                        f"{self.metrics.last_decision_lane or 'N/A'} |"
                    )

            lines.extend([
                "",
                "## Per-Lane EMA State",
                "",
                "| Lane | Current EMA | History Mean | Last 5 Raw |",
                "|------|-------------|--------------|------------|",
            ])

            for lane_name in ["North", "South", "East", "West"]:
                history = self.get_count_history(lane_name)
                ema = self.get_ema(lane_name)
                mean = sum(history) / len(history) if history else 0.0
                last5 = history[-5:] if len(history) >= 5 else history
                lines.append(
                    f"| {lane_name:<6} | {ema:<11.2f} | {mean:<12.2f} | {str(last5)} |"
                )

            lines.append("")

            with open(_REPORT_PATH, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            logger.info(f"Scheduler input report flushed to {_REPORT_PATH}")
            self._report_entries.clear()
            return _REPORT_PATH

        except Exception as e:
            logger.warning(f"Failed to flush scheduler input report: {e}")
            return None
