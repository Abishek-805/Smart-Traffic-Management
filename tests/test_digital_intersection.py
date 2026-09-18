"""
Unit and safety invariant test suite for the Digital Intersection State View and Simulation Engine.

Verifies:
1. Initial safe state before any camera connects (all-red clearance, zero countdown, cycle 0).
2. REST API endpoint GET /api/v1/system/digital-intersection contract and schema compliance.
3. Multi-phase progression under simulated traffic inputs (countdown decrement, clockwise cycle increment).
4. Safety invariants:
   - Mutual exclusion of green signals (never two greens simultaneously).
   - Yellow clearance always precedes red transition.
   - All-red clearance is enforced between conflicting green phases.
   - Active camera dropout triggers safe transition / all-red hold.
   - AI processing stall triggers immediate all-red hold.
"""

import pytest
from fastapi.testclient import TestClient

from web.app import app
from ai.pipeline.digital_intersection import DigitalIntersection, SignalColor, SafetyStatus
from core.application_context import ApplicationContext


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def digital_intersection():
    return DigitalIntersection(simulation_mode=True, min_green_sec=10, max_green_sec=60, yellow_sec=3, all_red_sec=2)


def test_initial_safe_state():
    """Verify digital intersection initializes in a safe default state before feeds arrive."""
    ctx = ApplicationContext.get_instance()
    # Digital intersection with live context but no active feeds
    intersection = DigitalIntersection(context=ctx, simulation_mode=False)
    snap = intersection.get_snapshot()

    assert "timestamp" in snap
    assert snap["active_phase"] == "all_red"
    assert snap["current_green_lane"] is None
    assert snap["current_yellow_lane"] is None
    assert snap["remaining_time_seconds"] == 0
    assert snap["cycle_count"] == 0
    assert snap["safety_status"] in (SafetyStatus.ALL_RED_HOLD.value, SafetyStatus.DEGRADED.value)

    # All 4 approaches present and RED
    approaches = snap["approaches"]
    assert set(approaches.keys()) == {"north", "east", "south", "west"}
    for name, app_data in approaches.items():
        assert app_data["signal"] == "RED"
        assert app_data["vehicles"] == 0
        assert app_data["queue"] == 0
        assert app_data["pce"] == 0.0


def test_api_endpoint_digital_intersection(client):
    """Verify GET /api/v1/system/digital-intersection returns expected structure and is publicly readable."""
    resp = client.get("/api/v1/system/digital-intersection")
    assert resp.status_code == 200

    body = resp.json()
    assert body.get("success") is True or "timestamp" in body

    # Check that required top-level or data-envelope fields exist
    snap = body.get("data", body)
    for field_key in [
        "timestamp",
        "active_phase",
        "current_green_lane",
        "current_yellow_lane",
        "remaining_time_seconds",
        "approaches",
        "safety_status",
        "cycle_count",
    ]:
        assert field_key in snap, f"Missing required snapshot field: {field_key}"

    approaches = snap["approaches"]
    assert set(approaches.keys()) == {"north", "east", "south", "west"}
    for name, data in approaches.items():
        assert "vehicles" in data
        assert "queue" in data
        assert "pce" in data
        assert "priority" in data
        assert "camera_status" in data
        assert "signal" in data
        assert data["signal"] in ("RED", "YELLOW", "GREEN")


def test_phase_progression_and_cycle_increment(digital_intersection):
    """
    Verify state machine advances under simulated demand:
    starts ALL_RED -> selects North GREEN -> counts down -> YELLOW -> ALL_RED -> East GREEN -> ...
    and increments cycle count.
    """
    # Provide demand on North and East
    demands = {
        "north": {"vehicles": 5, "queue": 2, "pce": 5.0, "has_priority": False},
        "east": {"vehicles": 3, "queue": 1, "pce": 3.0, "has_priority": False},
    }

    # Step 1: Initial step from ALL_RED selects highest priority approach (North)
    snap = digital_intersection.step_simulation(dt=0.1, lane_demands=demands)
    assert snap["active_phase"] == "north_green"
    assert snap["current_green_lane"] == "north"
    assert snap["approaches"]["north"]["signal"] == "GREEN"
    assert snap["approaches"]["east"]["signal"] == "RED"
    assert snap["approaches"]["south"]["signal"] == "RED"
    assert snap["approaches"]["west"]["signal"] == "RED"

    # Remaining time should be at least min_green (10s)
    initial_remaining = snap["remaining_time_seconds"]
    assert initial_remaining >= 10

    # Step 2: Advance time by 5s -> remaining time decreases, still green
    snap2 = digital_intersection.step_simulation(dt=5.0)
    assert snap2["active_phase"] == "north_green"
    assert snap2["remaining_time_seconds"] < initial_remaining

    # Step 3: Advance past green duration -> transitions to yellow
    rem = snap2["remaining_time_seconds"]
    snap3 = digital_intersection.step_simulation(dt=rem + 0.1)
    assert snap3["active_phase"] == "north_yellow"
    assert snap3["current_green_lane"] is None
    assert snap3["current_yellow_lane"] == "north"
    assert snap3["approaches"]["north"]["signal"] == "YELLOW"

    # Step 4: Advance past yellow duration (3s) -> transitions to all-red
    snap4 = digital_intersection.step_simulation(dt=3.1)
    assert snap4["active_phase"] == "all_red"
    assert snap4["approaches"]["north"]["signal"] == "RED"
    assert all(a["signal"] == "RED" for a in snap4["approaches"].values())

    # Step 5: Advance past all-red (2s) -> next approach with demand (East) turns green
    snap5 = digital_intersection.step_simulation(dt=2.1)
    assert snap5["active_phase"] == "east_green"
    assert snap5["approaches"]["east"]["signal"] == "GREEN"
    assert snap5["approaches"]["north"]["signal"] == "RED"


def test_safety_invariant_mutual_exclusion(digital_intersection):
    """
    CRITICAL SAFETY INVARIANT: Mutual Exclusion of Greens.
    At NO point in time may more than 1 approach exhibit GREEN or YELLOW.
    """
    demands = {
        "north": {"vehicles": 10, "queue": 4, "pce": 12.0, "has_priority": False},
        "east": {"vehicles": 8, "queue": 3, "pce": 9.0, "has_priority": False},
        "south": {"vehicles": 6, "queue": 2, "pce": 7.0, "has_priority": False},
        "west": {"vehicles": 4, "queue": 1, "pce": 5.0, "has_priority": False},
    }

    # Simulate 100 small increments across multiple phase cycles
    for _ in range(100):
        snap = digital_intersection.step_simulation(dt=1.0, lane_demands=demands)
        approaches = snap["approaches"]

        green_count = sum(1 for a in approaches.values() if a["signal"] == "GREEN")
        yellow_count = sum(1 for a in approaches.values() if a["signal"] == "YELLOW")

        assert green_count <= 1, f"Invariant violated: {green_count} green signals active simultaneously!"
        assert yellow_count <= 1, f"Invariant violated: {yellow_count} yellow signals active simultaneously!"
        assert (green_count + yellow_count) <= 1, (
            f"Invariant violated: conflicting active signals (green={green_count}, yellow={yellow_count})"
        )


def test_safety_invariant_camera_dropout_fallback(digital_intersection):
    """
    CRITICAL SAFETY INVARIANT: Camera Dropout Handling.
    If the active green camera drops out, system must immediately enter clearance to safe all-red.
    If all cameras drop out, system must enter and remain in ALL_RED_HOLD.
    """
    demands = {"north": {"vehicles": 5, "queue": 2, "pce": 6.0, "has_priority": False}}
    snap = digital_intersection.step_simulation(dt=0.1, lane_demands=demands)
    assert snap["active_phase"] == "north_green"

    # Simulate North camera dropout
    digital_intersection.trigger_camera_dropout("north", "OFFLINE")
    snap_after_drop = digital_intersection.get_snapshot()

    # Active green approach dropped out -> initiated clearance (YELLOW)
    assert snap_after_drop["active_phase"] in ("north_yellow", "all_red")
    assert snap_after_drop["safety_status"] == SafetyStatus.DEGRADED.value

    # Simulate all cameras dropping out
    for lane in ["north", "east", "south", "west"]:
        digital_intersection.trigger_camera_dropout(lane, "OFFLINE")

    snap_all_offline = digital_intersection.step_simulation(dt=5.0)
    assert snap_all_offline["active_phase"] == "all_red"
    assert snap_all_offline["safety_status"] == SafetyStatus.ALL_RED_HOLD.value
    assert all(a["signal"] == "RED" for a in snap_all_offline["approaches"].values())


def test_safety_invariant_ai_stall_fallback(digital_intersection):
    """
    CRITICAL SAFETY INVARIANT: AI Processing Stall Fallback.
    An AI perception or scheduler stall MUST immediately force ALL_RED_HOLD.
    """
    demands = {"east": {"vehicles": 4, "queue": 1, "pce": 4.0, "has_priority": False}}
    digital_intersection.step_simulation(dt=0.1, lane_demands=demands)

    # Trigger AI stall
    digital_intersection.trigger_ai_stall(stalled=True)
    snap = digital_intersection.step_simulation(dt=1.0)

    assert snap["active_phase"] == "all_red"
    assert snap["safety_status"] == SafetyStatus.ALL_RED_HOLD.value
    assert snap["current_green_lane"] is None
    assert snap["current_yellow_lane"] is None
    assert snap["remaining_time_seconds"] == 0
    assert all(a["signal"] == "RED" for a in snap["approaches"].values())
