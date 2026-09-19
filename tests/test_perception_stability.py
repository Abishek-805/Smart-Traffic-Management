from ai.analytics.analytics_exporter import AnalyticsExporter
from ai.detection.detection_types import Detection, ObservationState
from ai.state.vehicle_state_manager import VehicleStateManager


def detection(frame, timestamp, lane="North", observation=ObservationState.OBSERVED):
    return Detection(
        "car", 2, 0.9, (100, 100, 180, 180), track_id=7, lane=lane,
        frame_number=frame, timestamp=timestamp, observation_type=observation,
    )


def confirmed_count(manager):
    stats = AnalyticsExporter().generate_stats(manager)
    return sum(item.live_count for item in stats.values())


def test_short_occlusion_does_not_create_new_confirmed_count():
    manager = VehicleStateManager()
    counts = []
    manager.update([detection(1, 1.0)], 1, 1.0)
    counts.append(confirmed_count(manager))
    manager.update([detection(2, 1.5)], 2, 1.5)
    counts.append(confirmed_count(manager))
    manager.update([detection(3, 2.0, observation=ObservationState.PREDICTED)], 3, 2.0)
    counts.append(confirmed_count(manager))
    manager.update([detection(4, 2.5)], 4, 2.5)
    counts.append(confirmed_count(manager))

    assert max(counts) == 1
    assert manager.historical_tracks_count["North"] == {7}


def test_lane_switch_requires_repeated_observed_evidence():
    manager = VehicleStateManager()
    manager.update([detection(1, 1.0, "North")], 1, 1.0)
    manager.update([detection(2, 1.5, "North")], 2, 1.5)

    manager.update([detection(3, 2.0, "South")], 3, 2.0)
    assert manager.active_states[7].lane == "North"

    manager.update([detection(4, 2.5, "South", ObservationState.PREDICTED)], 4, 2.5)
    assert manager.active_states[7].lane == "North"

    manager.update([detection(5, 3.0, "South")], 5, 3.0)
    manager.update([detection(6, 3.5, "South")], 6, 3.5)
    assert manager.active_states[7].lane == "South"


def test_lane_switch_candidate_resets_when_observation_returns_to_current_lane():
    manager = VehicleStateManager()
    manager.update([detection(1, 1.0, "North")], 1, 1.0)
    manager.update([detection(2, 1.5, "North")], 2, 1.5)
    manager.update([detection(3, 2.0, "South")], 3, 2.0)
    manager.update([detection(4, 2.5, "North")], 4, 2.5)
    manager.update([detection(5, 3.0, "South")], 5, 3.0)
    manager.update([detection(6, 3.5, "South")], 6, 3.5)

    assert manager.active_states[7].lane == "North"
