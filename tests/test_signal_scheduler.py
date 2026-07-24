"""
Unit tests for SignalScheduler module.
"""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from ai.signal.signal_types import (
    LaneName,
    DecisionReason,
    PriorityBreakdown,
    PriorityScore,
    PriorityResult,
)
from ai.signal.signal_decision import SignalDecision
from ai.signal.signal_scheduler import SignalScheduler


def create_sample_priority_result(north_score: float = 40.0) -> PriorityResult:
    scores = [
        PriorityScore(
            lane=LaneName.NORTH,
            score=north_score,
            rank=1,
            breakdown=PriorityBreakdown(pce=20.0, queue=15.0, congestion=5.0),
        ),
        PriorityScore(
            lane=LaneName.SOUTH,
            score=20.0,
            rank=2,
            breakdown=PriorityBreakdown(pce=10.0, queue=8.0, congestion=2.0),
        ),
        PriorityScore(
            lane=LaneName.EAST,
            score=10.0,
            rank=3,
            breakdown=PriorityBreakdown(pce=5.0, queue=3.0, congestion=2.0),
        ),
        PriorityScore(
            lane=LaneName.WEST,
            score=5.0,
            rank=4,
            breakdown=PriorityBreakdown(pce=2.0, queue=2.0, congestion=1.0),
        ),
    ]
    return PriorityResult(scores=scores, highest_priority=scores[0])


def test_scheduler_winner_selection():
    scheduler = SignalScheduler(min_green_sec=10, max_green_sec=60)
    p_result = create_sample_priority_result(north_score=40.0)

    decision = scheduler.schedule(p_result, phase_id=1)

    assert isinstance(decision, SignalDecision)
    assert decision.phase_id == 1
    assert decision.green_lane == LaneName.NORTH
    assert set(decision.red_lanes) == {LaneName.SOUTH, LaneName.EAST, LaneName.WEST}
    assert decision.reason == DecisionReason.NORMAL
    assert decision.green_duration_sec > 10
    assert decision.green_duration_sec <= 60

    print("✔ Scheduler winner selection and phase_id test passed!")


if __name__ == "__main__":
    test_scheduler_winner_selection()
