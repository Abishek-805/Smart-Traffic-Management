"""
Property and Safety Invariant Tests.
Codifies critical mathematical, algorithmic, and operational invariants
that must never be violated under any input condition or system state.
"""

import time
import pytest
from ai.signal.signal_types import (
    LaneName,
    DecisionReason,
    PriorityBreakdown,
    PriorityScore,
    PriorityResult,
)
from ai.signal.signal_scheduler import SignalScheduler
from ai.signal.signal_controller import SignalController
from ai.analytics.analytics_exporter import LaneStatistics
from ai.detection.detection_types import Detection, ObservationState
from ai.state.vehicle_state_manager import VehicleStateManager
from server.frame_coordinator import process_batch
from core.application_context import ApplicationContext


def test_invariant_mutual_exclusion_of_greens():
    """
    INVARIANT 1: Mutual Exclusion.
    The signal controller must NEVER assign GREEN to more than one direction simultaneously.
    All non-green approaches must be designated as RED.
    """
    scheduler = SignalScheduler()
    controller = SignalController()

    scores = [
        PriorityScore(lane=LaneName.NORTH, score=50.0, rank=1, breakdown=PriorityBreakdown(50, 10, 5, 20.0, 50.0)),
        PriorityScore(lane=LaneName.EAST, score=30.0, rank=2, breakdown=PriorityBreakdown(30, 5, 2, 10.0, 20.0)),
        PriorityScore(lane=LaneName.SOUTH, score=20.0, rank=3, breakdown=PriorityBreakdown(20, 5, 2, 5.0, 10.0)),
        PriorityScore(lane=LaneName.WEST, score=10.0, rank=4, breakdown=PriorityBreakdown(10, 2, 1, 2.0, 5.0)),
    ]
    priority_res = PriorityResult(scores=scores, highest_priority=scores[0])

    decision = scheduler.schedule(priority_res, phase_id=1)
    cmd = controller.generate_command(decision)

    # Invariant checks
    assert cmd.green_lane == LaneName.NORTH
    assert LaneName.NORTH not in cmd.red_lanes
    assert len(cmd.red_lanes) == 3
    assert set(cmd.red_lanes) == {LaneName.EAST, LaneName.SOUTH, LaneName.WEST}


def test_invariant_clearance_intervals_preservation():
    """
    INVARIANT 2: Minimum Clearance Interval.
    Yellow duration must be >= 3s, and clearance must be enforced.
    """
    scheduler = SignalScheduler(yellow_sec=3)
    scores = [PriorityScore(lane=LaneName.NORTH, score=20.0, rank=1, breakdown=PriorityBreakdown(10, 5, 2, 5.0, 10.0))]
    decision = scheduler.schedule(PriorityResult(scores=scores, highest_priority=scores[0]))

    assert decision.yellow_duration_sec >= 3


def test_invariant_green_time_strictly_clamped():
    """
    INVARIANT 3: Green Allocation Clamping Bounds.
    Allocated green time must ALWAYS lie strictly within [MIN_GREEN_SEC, MAX_GREEN_SEC],
    even under extreme edge cases (zero demand, negative demand, infinite demand).
    """
    scheduler = SignalScheduler(min_green_sec=10, max_green_sec=60)

    # Case A: Minimal/Zero Demand
    zero_score = PriorityScore(lane=LaneName.NORTH, score=0.0, rank=1, breakdown=PriorityBreakdown(0, 0, 0, 0.0, 0.0))
    zero_res = PriorityResult(scores=[zero_score], highest_priority=zero_score)
    green_zero = scheduler._calculate_green_time(zero_score, zero_res)
    assert green_zero == 10  # Clamped to min_green

    # Case B: Massive / Overwhelming Demand
    huge_score = PriorityScore(
        lane=LaneName.NORTH,
        score=999999.0,
        rank=1,
        breakdown=PriorityBreakdown(pce=99999, queue=99999, congestion=99999, raw_pce=100.0, raw_queue_sec=1000.0),
    )
    huge_res = PriorityResult(scores=[huge_score], highest_priority=huge_score)
    green_huge = scheduler._calculate_green_time(huge_score, huge_res)
    assert green_huge == 60  # Clamped to max_green

    # Case C: Boundary test across spectrum [0 to 1000]
    for test_pce in [0.1, 1.0, 5.0, 10.0, 20.0, 50.0, 500.0]:
        sc = PriorityScore(lane=LaneName.EAST, score=test_pce, rank=1, breakdown=PriorityBreakdown(pce=test_pce, queue=0, congestion=0, raw_pce=test_pce, raw_queue_sec=0))
        pr = PriorityResult(scores=[sc], highest_priority=sc)
        g_time = scheduler._calculate_green_time(sc, pr)
        assert 10 <= g_time <= 60, f"Green time {g_time} out of bounds for PCE {test_pce}"


def test_invariant_bounded_starvation_guarantee():
    """
    INVARIANT 4: Bounded Wait Time (Anti-Starvation).
    In clockwise adaptive cycling, an approach with demand must be served
    in at most 4 phase steps, even if an opposing approach has 100x higher demand.
    """
    scheduler = SignalScheduler()
    fresh = ["north", "south", "east", "west"]

    # North has massive continuous demand
    north_stats = LaneStatistics(lane_name="north", raw_count=50, pce_score=60.0)
    # South has tiny demand (1 car)
    south_stats = LaneStatistics(lane_name="south", raw_count=1, pce_score=1.0)
    east_stats = LaneStatistics(lane_name="east", raw_count=1, pce_score=1.0)
    west_stats = LaneStatistics(lane_name="west", raw_count=1, pce_score=1.0)

    stats = {"north": north_stats, "south": south_stats, "east": east_stats, "west": west_stats}

    p_scores = [
        PriorityScore(lane=LaneName.NORTH, score=100.0, rank=1, breakdown=PriorityBreakdown(60, 0, 0, raw_pce=60, raw_queue_sec=0)),
        PriorityScore(lane=LaneName.EAST, score=2.0, rank=2, breakdown=PriorityBreakdown(1, 0, 0, raw_pce=1, raw_queue_sec=0)),
        PriorityScore(lane=LaneName.SOUTH, score=2.0, rank=3, breakdown=PriorityBreakdown(1, 0, 0, raw_pce=1, raw_queue_sec=0)),
        PriorityScore(lane=LaneName.WEST, score=2.0, rank=4, breakdown=PriorityBreakdown(1, 0, 0, raw_pce=1, raw_queue_sec=0)),
    ]
    p_res = PriorityResult(scores=p_scores, highest_priority=p_scores[0])

    served_order = []
    for _ in range(4):
        eligible, _ = scheduler.select_eligible(p_res, stats, fresh)
        assert eligible is not None
        winner = eligible.highest_priority
        lane_str = getattr(winner.lane, "value", str(winner.lane)).lower()
        served_order.append(lane_str)

    # All 4 lanes must have been served exactly once!
    assert set(served_order) == {"north", "east", "south", "west"}
    assert len(set(served_order)) == 4


def test_invariant_prediction_immunity():
    """
    INVARIANT 5: Prediction Immunity.
    Detections marked as ObservationState.PREDICTED must NEVER increment
    the confirmed vehicle count in VehicleStateManager.
    """
    state_mgr = VehicleStateManager()

    # Step 1: Feed a single PREDICTED detection
    pred_det = Detection(
        class_name="car",
        class_id=2,
        confidence=0.90,
        bbox=(100, 100, 200, 200),
        track_id=42,
        frame_number=1,
        timestamp=100.0,
        observation_type=ObservationState.PREDICTED,
    )

    state_mgr.update([pred_det], frame_number=1, timestamp=100.0)

    # Invariant: confirmed active_states must remain empty!
    assert len(state_mgr.active_states) == 0, "Predicted detection was incorrectly converted to active vehicle"


def test_invariant_stale_frame_rejection():
    """
    INVARIANT 6: Stale Frame Rejection.
    Frames arriving with latency > 2500 ms must be dropped by frame coordination.
    """
    ctx = ApplicationContext.get_instance()
    ctx.system_running = True
    initial_dropped = ctx.get_stage_counters()["dropped"]

    stale_timestamp_ms = (time.time() - 3.0) * 1000  # 3000ms old

    packet = {
        "payload": {
            "direction": "north",
            "frame_data": "dummy",
            "capture_timestamp": stale_timestamp_ms,
            "frame_id": "stale_01",
        },
        "backend_receive_timestamp": stale_timestamp_ms,
    }

    # Process batch with the stale packet
    results = process_batch([packet])

    # Result should be empty and dropped counter incremented
    assert len(results) == 0
    assert ctx.get_stage_counters()["dropped"] > initial_dropped
