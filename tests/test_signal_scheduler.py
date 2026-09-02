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
from ai.analytics.analytics_exporter import LaneStatistics


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


def _lane_stats(counts, emergency=None):
    emergency = emergency or set()
    return {name: LaneStatistics(lane_name=name, live_count=count, raw_count=count,
        has_priority_vehicle=name in emergency) for name, count in counts.items()}


def test_scheduler_excludes_stale_approaches():
    scheduler = SignalScheduler()
    result = create_sample_priority_result(north_score=100)
    stats = _lane_stats({'north': 8, 'south': 3, 'east': 2, 'west': 1})
    selected, starvation = scheduler.select_eligible(result, stats, {'south', 'east'},
        {'North': 0, 'South': 0, 'East': 0, 'West': 0})
    assert selected.highest_priority.lane == LaneName.EAST
    assert not starvation


def test_scheduler_serves_each_occupied_lane_once_in_clockwise_cycle():
    scheduler = SignalScheduler()
    result = create_sample_priority_result(north_score=100)
    stats = _lane_stats({'north': 40, 'south': 1, 'east': 2, 'west': 1})
    served = []
    for _ in range(4):
        selected, starvation = scheduler.select_eligible(
            result, stats, {'north', 'south', 'east', 'west'})
        served.append(selected.highest_priority.lane)
        assert not starvation
    assert served == [LaneName.NORTH, LaneName.EAST, LaneName.SOUTH, LaneName.WEST]


def test_scheduler_skips_empty_lanes_without_allocating_minimum_green():
    scheduler = SignalScheduler()
    result = create_sample_priority_result(north_score=100)
    stats = _lane_stats({'north': 0, 'south': 2, 'east': 0, 'west': 0})
    selected, _ = scheduler.select_eligible(result, stats, {'north', 'south', 'east', 'west'})
    assert selected.highest_priority.lane == LaneName.SOUTH
    stats['south'].raw_count = 0
    selected, _ = scheduler.select_eligible(result, stats, {'north', 'south', 'east', 'west'})
    assert selected is None


def test_emergency_preempts_starvation_only_when_fresh():
    scheduler = SignalScheduler()
    result = create_sample_priority_result(north_score=100)
    stats = _lane_stats({'north': 8, 'south': 1}, emergency={'north'})
    selected, starvation = scheduler.select_eligible(result, stats, {'north', 'south'},
        {'North': 0, 'South': 4})
    assert selected.highest_priority.lane == LaneName.NORTH
    assert not starvation
    selected, starvation = scheduler.select_eligible(result, stats, {'south'},
        {'North': 0, 'South': 4})
    assert selected.highest_priority.lane == LaneName.SOUTH
    assert not starvation


def test_adaptive_green_uses_absolute_demand_and_stays_bounded():
    scheduler = SignalScheduler(min_green_sec=10, max_green_sec=60)
    result = create_sample_priority_result(north_score=100)
    north = next(score for score in result.scores if score.lane == LaneName.NORTH)
    north.breakdown.raw_pce = 1.0
    north.breakdown.raw_queue_sec = 0.0
    low = scheduler.schedule(result).green_duration_sec
    north.breakdown.raw_pce = 20.0
    north.breakdown.raw_queue_sec = 120.0
    high = scheduler.schedule(result).green_duration_sec
    assert 10 <= low < high <= 60


if __name__ == "__main__":
    test_scheduler_winner_selection()
