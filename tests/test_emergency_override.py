"""
Unit tests for EmergencyOverride and capped fairness bonus.
"""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from ai.signal import (
    LaneName,
    PriorityBreakdown,
    PriorityScore,
    PriorityResult,
    FairnessManager,
    EmergencyOverride,
    SignalScheduler,
)
from ai.analytics.analytics_exporter import LaneStatistics


def test_fairness_cap():
    print("=== Test 1: Fairness Bonus Cap ===")
    bd = PriorityBreakdown(pce=5.0, queue=5.0, congestion=5.0)

    fairness = FairnessManager(bonus_per_cycle=5.0, max_bonus=25.0)
    fairness.cycles_since_served["South"] = 100  # 100 * 5.0 = 500.0, should cap at 25.0

    scores = [
        PriorityScore(lane=LaneName.SOUTH, score=5.0, rank=1, breakdown=bd),
    ]
    res = PriorityResult(scores=scores, highest_priority=scores[0])

    adjusted = fairness.apply_fairness(res)
    assert adjusted.scores[0].breakdown.fairness_bonus == 25.0
    assert adjusted.scores[0].score == 30.0
    print("✔ Fairness bonus cap test passed! 100 waiting cycles capped at +25.0 max bonus.")


def test_emergency_override():
    print("\n=== Test 2: Emergency Vehicle Override ===")
    bd = PriorityBreakdown(pce=5.0, queue=5.0, congestion=5.0)

    # Base demand: North has high demand (40.0), South has low demand (5.0)
    scores = [
        PriorityScore(lane=LaneName.NORTH, score=40.0, rank=1, breakdown=bd),
        PriorityScore(lane=LaneName.SOUTH, score=5.0, rank=2, breakdown=bd),
    ]
    raw_res = PriorityResult(scores=scores, highest_priority=scores[0])

    # Analytics stats reporting ambulance in South lane
    mock_stats = {
        "North": LaneStatistics("North", 15, 20.0, 5, 20.0, 10.0, 5.0, 30.0, "HIGH", 50, has_priority_vehicle=False),
        "South": LaneStatistics("South", 1, 1.0, 0, 0.0, 0.0, 40.0, 1.0, "LOW", 5, has_priority_vehicle=True),
    }

    override = EmergencyOverride(boost_score=1000.0)
    overridden_res = override.check_and_override(raw_res, mock_stats)

    # South must win Rank #1 due to emergency override
    assert overridden_res.highest_priority.lane == LaneName.SOUTH
    assert overridden_res.scores[0].score == 1005.0
    print("✔ Emergency override test passed! Ambulance in South lane boosted to Rank #1 (Score: 1005.0).")


def test_full_decision_pipeline():
    print("\n=== Test 3: Full Decision Pipeline with Emergency Override ===")
    bd = PriorityBreakdown(pce=5.0, queue=5.0, congestion=5.0)

    fairness = FairnessManager(bonus_per_cycle=5.0, max_bonus=25.0)
    override = EmergencyOverride(boost_score=1000.0)
    scheduler = SignalScheduler()

    # Base Scores
    scores = [
        PriorityScore(lane=LaneName.NORTH, score=50.0, rank=1, breakdown=bd),
        PriorityScore(lane=LaneName.WEST, score=10.0, rank=2, breakdown=bd),
    ]
    raw_res = PriorityResult(scores=scores, highest_priority=scores[0])

    # Analytics reporting fire truck in West lane
    mock_stats = {
        "North": LaneStatistics("North", 20, 25.0, 10, 40.0, 20.0, 2.0, 45.0, "CONGESTED", 80, has_priority_vehicle=False),
        "West": LaneStatistics("West", 1, 2.0, 0, 0.0, 0.0, 35.0, 2.0, "LOW", 12, has_priority_vehicle=True),
    }

    # Pipeline Flow: Base -> Fairness -> EmergencyOverride -> Scheduler
    fairness_res = fairness.apply_fairness(raw_res)
    override_res = override.check_and_override(fairness_res, mock_stats)
    decision = scheduler.schedule(override_res)

    assert decision.green_lane == LaneName.WEST
    print(f"✔ Pipeline decision generated: Green granted to '{decision.green_lane.value}' for {decision.green_duration_sec}s.")


if __name__ == "__main__":
    test_fairness_cap()
    test_emergency_override()
    test_full_decision_pipeline()
    print("\n🎉 ALL EMERGENCYOVERRIDE UNIT TESTS PASSED SUCCESSFULLY!")
