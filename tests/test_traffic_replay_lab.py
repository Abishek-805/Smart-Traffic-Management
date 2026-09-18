"""
Tests for Traffic Replay Lab simulation and scenario execution.
"""

import pytest
from ai.pipeline.replay_lab import TrafficReplayLab, TrafficScenario


def test_replay_lab_balanced_normal_scenario():
    lab = TrafficReplayLab(min_green=10, max_green=60, yellow_sec=3)
    result = lab.run_scenario(TrafficScenario.BALANCED_NORMAL, total_steps=8)

    assert result.total_steps == 8
    assert len(result.steps) == 8
    assert result.emergency_preemptions == 0
    assert result.disconnected_dropouts == 0

    # In balanced traffic, clockwise cycle serves each lane equally (2 times each over 8 steps)
    alloc = result.green_allocations_by_lane
    assert alloc["north"] == 2
    assert alloc["east"] == 2
    assert alloc["south"] == 2
    assert alloc["west"] == 2

    # Check that green durations are within [10, 60]
    for step in result.steps:
        assert 10 <= step.green_duration_sec <= 60
        assert step.yellow_duration_sec == 3


def test_replay_lab_heavy_north_adaptive_timing():
    lab = TrafficReplayLab(min_green=10, max_green=60, yellow_sec=3)
    result = lab.run_scenario(TrafficScenario.HEAVY_NORTH, total_steps=4)

    # All 4 approaches are served in 1 round
    assert result.total_steps == 4
    alloc = result.green_allocations_by_lane
    assert alloc["north"] == 1

    # North has heavy load (PCE 24, queue 110s) -> should receive near maximum green (> 40s)
    north_step = next(s for s in result.steps if s.active_green_lane == "north")
    assert north_step.green_duration_sec >= 40

    # East/South/West have light load (PCE 2) -> should receive minimum green (10s)
    east_step = next(s for s in result.steps if s.active_green_lane == "east")
    assert east_step.green_duration_sec <= 15


def test_replay_lab_emergency_preemption():
    lab = TrafficReplayLab(min_green=10, max_green=60, yellow_sec=3)
    # 4 steps: emergency activates at step 2 on South
    result = lab.run_scenario(TrafficScenario.EMERGENCY_PREEMPTION, total_steps=4)

    assert result.emergency_preemptions > 0
    # Step 2 must be South because emergency preemption interrupts normal sequence
    assert result.steps[2].active_green_lane == "south"


def test_replay_lab_camera_disconnect_dropout():
    lab = TrafficReplayLab(min_green=10, max_green=60, yellow_sec=3)
    # 6 steps: East drops after step 3
    result = lab.run_scenario(TrafficScenario.CAMERA_DISCONNECT, total_steps=6)

    assert result.disconnected_dropouts > 0
    # Steps after step 3 should skip East and continue cycling North, South, West
    for s in result.steps[4:]:
        assert s.active_green_lane != "east"
