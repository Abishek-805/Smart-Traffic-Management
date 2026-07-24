"""
Unit tests for FairnessManager module.
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
    PriorityCalculator,
    SignalScheduler,
)


def test_fairness_initial():
    print("=== Test 1: Initial Fairness (No Wait Cycles) ===")
    bd = PriorityBreakdown(pce=5.0, queue=5.0, congestion=5.0)

    scores = [
        PriorityScore(lane=LaneName.NORTH, score=20.0, rank=1, breakdown=bd),
        PriorityScore(lane=LaneName.SOUTH, score=5.0, rank=2, breakdown=bd),
    ]
    res = PriorityResult(scores=scores, highest_priority=scores[0])

    fairness = FairnessManager(bonus_per_cycle=5.0)
    adjusted_res = fairness.apply_fairness(res)

    assert adjusted_res.highest_priority.lane == LaneName.NORTH
    assert adjusted_res.scores[0].score == 20.0
    assert adjusted_res.scores[1].score == 5.0
    print("✔ Initial fairness test passed! Scores unchanged on initial run.")


def test_fairness_cycle_updates():
    print("\n=== Test 2: Cycle Updates and Waiting Bonuses ===")
    bd = PriorityBreakdown(pce=5.0, queue=5.0, congestion=5.0)

    fairness = FairnessManager(bonus_per_cycle=5.0)

    # Cycle 1: North wins
    fairness.update_served(LaneName.NORTH)
    assert fairness.cycles_since_served["North"] == 0
    assert fairness.cycles_since_served["South"] == 1
    assert fairness.cycles_since_served["East"] == 1
    assert fairness.cycles_since_served["West"] == 1

    # Cycle 2: North wins again
    fairness.update_served(LaneName.NORTH)
    assert fairness.cycles_since_served["North"] == 0
    assert fairness.cycles_since_served["South"] == 2
    assert fairness.cycles_since_served["East"] == 2
    assert fairness.cycles_since_served["West"] == 2

    print("✔ Cycle counters updated correctly across multiple cycles.")


def test_starvation_override():
    print("\n=== Test 3: Starvation Override ===")
    bd = PriorityBreakdown(pce=5.0, queue=5.0, congestion=5.0)

    fairness = FairnessManager(bonus_per_cycle=5.0)

    # Simulate South waiting for 5 consecutive cycles
    fairness.cycles_since_served["North"] = 0
    fairness.cycles_since_served["South"] = 5  # Bonus = 5 * 5.0 = 25.0

    # Base Scores: North = 20.0, South = 5.0
    scores = [
        PriorityScore(lane=LaneName.NORTH, score=20.0, rank=1, breakdown=bd),
        PriorityScore(lane=LaneName.SOUTH, score=5.0, rank=2, breakdown=bd),
    ]
    raw_res = PriorityResult(scores=scores, highest_priority=scores[0])

    adjusted_res = fairness.apply_fairness(raw_res)

    # South adjusted score: 5.0 + 25.0 = 30.0 > North 20.0
    assert adjusted_res.highest_priority.lane == LaneName.SOUTH
    assert adjusted_res.scores[0].score == 30.0
    assert adjusted_res.scores[0].breakdown.fairness_bonus == 25.0
    print("✔ Starvation override test passed! Low-demand South lane with wait bonus wins green over North.")


def test_pipeline_integration():
    print("\n=== Test 4: Pipeline Encapsulation Integration ===")
    bd = PriorityBreakdown(pce=5.0, queue=5.0, congestion=5.0)

    fairness = FairnessManager(bonus_per_cycle=5.0)
    scheduler = SignalScheduler()

    fairness.cycles_since_served["South"] = 4  # Bonus = +20.0

    scores = [
        PriorityScore(lane=LaneName.NORTH, score=15.0, rank=1, breakdown=bd),
        PriorityScore(lane=LaneName.SOUTH, score=5.0, rank=2, breakdown=bd),
    ]
    raw_res = PriorityResult(scores=scores, highest_priority=scores[0])

    # Pipeline Flow: PriorityResult -> FairnessManager -> PriorityResult -> SignalScheduler -> SignalDecision
    adjusted_res = fairness.apply_fairness(raw_res)
    decision = scheduler.schedule(adjusted_res)

    assert decision.green_lane == LaneName.SOUTH
    print(f"✔ Decision scheduled: Winner is '{decision.green_lane.value}' for {decision.green_duration_sec}s.")

    # Update served state after decision
    fairness.update_served(decision.green_lane)
    assert fairness.cycles_since_served["South"] == 0
    assert fairness.cycles_since_served["North"] == 1
    print("✔ Fairness state updated after scheduling.")


if __name__ == "__main__":
    test_fairness_initial()
    test_fairness_cycle_updates()
    test_starvation_override()
    test_pipeline_integration()
    print("\n🎉 ALL FAIRNESSMANAGER UNIT TESTS PASSED SUCCESSFULLY!")
