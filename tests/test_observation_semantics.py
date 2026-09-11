"""Regression tests separating detector evidence from tracker-only projections."""

from ai.analytics.analytics_exporter import AnalyticsExporter
from ai.detection.detection_types import Detection, ObservationState
from ai.state.vehicle_state_manager import VehicleStateManager
from ai.tracking.byte_tracker import ByteTracker


def _vehicle(*, x=10, timestamp=1.0, observation_type=ObservationState.OBSERVED):
    return Detection(
        "car", 2, 0.9, (x, 10, x + 60, 70), track_id=7, lane="North",
        frame_number=int(timestamp * 10), timestamp=timestamp,
        observation_type=observation_type,
    )


def test_tracker_marks_detector_evidence_and_projection_explicitly():
    tracker = ByteTracker()
    observed = tracker.update([Detection("car", 2, 0.9, (10, 10, 70, 70))], timestamp=1.0)
    predicted = tracker.predict(timestamp=1.1)

    assert observed[0].observation_type == ObservationState.OBSERVED
    assert predicted[0].observation_type == ObservationState.PREDICTED
    assert predicted[0].to_dict()["observation_type"] == "PREDICTED"


def test_predictions_do_not_confirm_or_refresh_vehicle_state():
    manager = VehicleStateManager()
    manager.update([_vehicle(timestamp=1.0)], frame_number=10, timestamp=1.0)
    original = manager.active_states[7]
    original_seen = original.last_seen_timestamp
    original_queue_frames = original.consecutive_low_motion_frames

    manager.update(
        [_vehicle(timestamp=1.1, observation_type=ObservationState.PREDICTED)],
        frame_number=11,
        timestamp=1.1,
    )

    state = manager.active_states[7]
    assert not state.is_confirmed
    assert not state.is_alive
    assert state.consecutive_seen_frames == 1
    assert state.last_seen_timestamp == original_seen
    assert state.consecutive_low_motion_frames == original_queue_frames
    assert state.observation_type == ObservationState.PREDICTED
    assert state.last_observation_frame_id == 10
    assert state.last_prediction_frame_id == 11
    assert state.last_observation_timestamp == 1.0


def test_only_confirmed_observations_feed_counts_and_queue_analytics():
    manager = VehicleStateManager()
    exporter = AnalyticsExporter()

    manager.update([_vehicle(timestamp=1.0)], frame_number=10, timestamp=1.0)
    assert exporter.generate_stats(manager)["North"].live_count == 0

    manager.update([_vehicle(timestamp=1.1)], frame_number=11, timestamp=1.1)
    assert exporter.generate_stats(manager)["North"].live_count == 1

    manager.update(
        [_vehicle(timestamp=1.2, observation_type=ObservationState.PREDICTED)],
        frame_number=12,
        timestamp=1.2,
    )
    predicted_stats = exporter.generate_stats(manager)["North"]
    assert predicted_stats.live_count == 0
    assert predicted_stats.total_queue_time_sec == 0
