"""
Unit tests for SignalScheduler module.
"""

import sys
from pathlib import Path
import pytest

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from ai.signal import (
    LaneName,
    DecisionReason,
    PriorityBreakdown,
    PriorityScore,
    PriorityResult,
    SignalDecision,
    SignalScheduler,
)


def test_clear_winner():
    print("=== Test 1: Clear Winner ===")
    bd = PriorityBreakdown(pce=5.0, queue=5.0, congestion=5.0)

    scores = [
        PriorityScore(lane=LaneName.NORTH, score=22.25, rank=1, breakdown=bd),
        PriorityScore(lane=LaneName.EAST, score=9.18, rank=2, breakdown=bd),
        PriorityScore(lane=LaneName.WEST, score=4.75, rank=3, breakdown=bd),
        PriorityScore(lane=LaneName.SOUTH, score=1.30, rank=4, breakdown=bd),
    ]
    res = PriorityResult(scores=scores, highest_priority=scores[0])

    scheduler = SignalScheduler(min_green_sec=10, max_green_sec=60, yellow_sec=3)
    decision = scheduler.schedule(res)

    assert isinstance(decision, SignalDecision)
    assert decision.green_lane == LaneName.NORTH
    assert decision.yellow_duration_sec == 3
    assert set(decision.red_lanes) == {LaneName.EAST, LaneName.WEST, LaneName.SOUTH}

    # Total score = 37.48. Ratio = 22.25 / 37.48 = 0.5936
    # Duration = 10 + 0.5936 * 50 = 39.68 -> 40s
    assert decision.green_duration_sec == 40
    print(f"✔ Clear winner test passed! Green duration: {decision.green_duration_sec}s")


def test_equal_scores():
    print("=== Test 2: Equal Scores ===")
    bd = PriorityBreakdown(pce=5.0, queue=5.0, congestion=5.0)

    scores = [
        PriorityScore(lane=LaneName.NORTH, score=15.0, rank=1, breakdown=bd),
        PriorityScore(lane=LaneName.SOUTH, score=15.0, rank=2, breakdown=bd),
    ]
    res = PriorityResult(scores=scores, highest_priority=scores[0])

    scheduler = SignalScheduler(min_green_sec=10, max_green_sec=60)
    decision = scheduler.schedule(res)

    assert decision.green_lane == LaneName.NORTH
    # Ratio = 15 / 30 = 0.5 -> Duration = 10 + 0.5 * 50 = 35s
    assert decision.green_duration_sec == 35
    print("✔ Equal scores test passed!")


def test_all_zero_scores():
    print("=== Test 3: All Zero Scores ===")
    bd = PriorityBreakdown(pce=0.0, queue=0.0, congestion=0.0)

    scores = [
        PriorityScore(lane=LaneName.EAST, score=0.0, rank=1, breakdown=bd),
        PriorityScore(lane=LaneName.WEST, score=0.0, rank=2, breakdown=bd),
    ]
    res = PriorityResult(scores=scores, highest_priority=scores[0])

    scheduler = SignalScheduler(min_green_sec=10, max_green_sec=60)
    decision = scheduler.schedule(res)

    assert decision.green_lane == LaneName.EAST
    assert decision.green_duration_sec == 10  # MIN_GREEN_SEC fallback
    print("✔ All zero scores test passed!")


def test_single_lane():
    print("=== Test 4: Single Lane ===")
    bd = PriorityBreakdown(pce=10.0, queue=0.0, congestion=0.0)

    scores = [
        PriorityScore(lane=LaneName.NORTH, score=10.0, rank=1, breakdown=bd),
    ]
    res = PriorityResult(scores=scores, highest_priority=scores[0])

    scheduler = SignalScheduler(min_green_sec=10, max_green_sec=60)
    decision = scheduler.schedule(res)

    assert decision.green_lane == LaneName.NORTH
    assert decision.red_lanes == []
    # Ratio = 10 / 10 = 1.0 -> Duration = 10 + 1.0 * 50 = 60s (MAX_GREEN_SEC)
    assert decision.green_duration_sec == 60
    print("✔ Single lane test passed!")


def test_empty_input():
    print("=== Test 5: Empty Input ===")
    scheduler = SignalScheduler()

    empty_res = PriorityResult(scores=[], highest_priority=None)

    with pytest.raises(ValueError):
        scheduler.schedule(empty_res)

    with pytest.raises(ValueError):
        scheduler.schedule(None)

    print("✔ Empty input exception test passed!")


def run_all_tests():
    test_clear_winner()
    test_equal_scores()
    test_all_zero_scores()
    test_single_lane()
    test_empty_input()
    print("\n🎉 ALL SIGNALSCHEDULER UNIT TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_clear_winner()
    test_equal_scores()
    test_all_zero_scores()
    test_single_lane()
    test_empty_input()
