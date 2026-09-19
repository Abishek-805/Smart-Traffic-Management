"""
VehicleStateManager maintains state, motion estimation, time-in-lane, and queue detection across frames.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import time

from ai.detection.detection_types import Detection, ObservationState
from config.traffic import (
    QUEUE_MOTION_THRESHOLD_PX_SEC,
    CONSECUTIVE_QUEUE_FRAMES,
    TRACK_EXPIRATION_TIMEOUT_SEC,
    MIN_CONFIRMATION_FRAMES,
    TRACK_REMOVAL_GRACE_SEC,
    LANE_SWITCH_CONFIRMATION_FRAMES,
)
from ai.utils.logger import get_logger

logger = get_logger("VehicleStateManager")


@dataclass
class VehicleState:
    """
    Mutable state tracker for a single vehicle track_id.
    """
    track_id: int
    class_name: str
    lane: str
    last_centroid: Tuple[int, int]
    first_seen_timestamp: float
    last_seen_timestamp: float
    entered_frame: int
    last_seen_frame: int
    motion_px_sec: float = 0.0
    time_in_lane_sec: float = 0.0
    queue_time_sec: float = 0.0
    consecutive_low_motion_frames: int = 0
    consecutive_seen_frames: int = 1  # Phase 3.5: track how many frames this vehicle has appeared in
    is_queued: bool = False
    is_alive: bool = True
    is_confirmed: bool = False        # Phase 3.5: True once consecutive_seen_frames >= MIN_CONFIRMATION_FRAMES
    is_priority: bool = False
    observation_type: ObservationState = ObservationState.OBSERVED
    last_observation_frame_id: int = 0
    last_prediction_frame_id: Optional[int] = None
    last_observation_timestamp: float = 0.0
    pending_lane: Optional[str] = None
    pending_lane_observations: int = 0


class VehicleStateManager:
    """
    Tracks vehicle state lifecycles, estimates motion, tracks queue time, and handles track expiration.
    """

    def __init__(self):
        self.active_states: Dict[int, VehicleState] = {}
        self.historical_tracks_count: Dict[str, set] = {
            "North": set(),
            "South": set(),
            "East": set(),
            "West": set(),
        }
        self.min_confirmation_frames = MIN_CONFIRMATION_FRAMES
        self.track_removal_grace_sec = TRACK_REMOVAL_GRACE_SEC

    def update(
        self,
        detections: List[Detection],
        frame_number: int,
        timestamp: float,
    ) -> List[Detection]:
        """
        Update vehicle state records with frame detections and enrich Detection objects.
        """
        current_frame_track_ids = set()

        for det in detections:
            if det.track_id is None:
                continue

            tid = det.track_id
            if det.observation_type == ObservationState.PREDICTED:
                # Tracker projections are visualization continuity, not new
                # evidence. Never confirm, refresh, or grow queues from them.
                predicted_state = self.active_states.get(tid)
                if predicted_state is not None:
                    predicted_state.observation_type = ObservationState.PREDICTED
                    predicted_state.last_prediction_frame_id = frame_number
                    det.motion_px_sec = predicted_state.motion_px_sec
                    det.time_in_lane_sec = predicted_state.time_in_lane_sec
                    det.queue_time_sec = predicted_state.queue_time_sec
                    det.is_priority = predicted_state.is_priority
                continue

            current_frame_track_ids.add(tid)
            lane_name = det.lane or "Unknown"

            cx, cy = det.centroid

            if tid not in self.active_states:
                # Initialize new vehicle state record
                state = VehicleState(
                    track_id=tid,
                    class_name=det.class_name,
                    lane=lane_name,
                    last_centroid=(cx, cy),
                    first_seen_timestamp=timestamp,
                    last_seen_timestamp=timestamp,
                    entered_frame=frame_number,
                    last_seen_frame=frame_number,
                    is_priority=det.is_priority,
                    observation_type=ObservationState.OBSERVED,
                    last_observation_frame_id=frame_number,
                    last_observation_timestamp=timestamp,
                )
                self.active_states[tid] = state
            else:
                state = self.active_states[tid]
                dt = timestamp - state.last_seen_timestamp
                
                # Check for lane transition
                if state.lane != lane_name:
                    if state.pending_lane == lane_name:
                        state.pending_lane_observations += 1
                    else:
                        state.pending_lane = lane_name
                        state.pending_lane_observations = 1
                    if state.pending_lane_observations >= LANE_SWITCH_CONFIRMATION_FRAMES:
                        logger.info(f"Vehicle #{tid} switched lane: '{state.lane}' -> '{lane_name}'")
                        state.lane = lane_name
                        state.pending_lane = None
                        state.pending_lane_observations = 0
                        state.time_in_lane_sec = 0.0
                        state.queue_time_sec = 0.0
                        state.consecutive_low_motion_frames = 0
                else:
                    state.pending_lane = None
                    state.pending_lane_observations = 0
                    if dt > 0:
                        state.time_in_lane_sec += dt

                # Compute motion_px_sec (relative pixel displacement over time)
                prev_cx, prev_cy = state.last_centroid
                dist_px = math.hypot(cx - prev_cx, cy - prev_cy)
                
                if dt > 0:
                    state.motion_px_sec = dist_px / dt

                # Consecutive-frame queue detection
                if state.motion_px_sec < QUEUE_MOTION_THRESHOLD_PX_SEC:
                    state.consecutive_low_motion_frames += 1
                else:
                    state.consecutive_low_motion_frames = max(0, state.consecutive_low_motion_frames - 1)

                # Flag queued status if low motion persists for N consecutive frames
                if state.consecutive_low_motion_frames >= CONSECUTIVE_QUEUE_FRAMES:
                    state.is_queued = True
                    if dt > 0:
                        state.queue_time_sec += dt
                else:
                    state.is_queued = False

                # Phase 3.5: Increment seen frames and mark confirmed if threshold met
                state.consecutive_seen_frames += 1
                if state.consecutive_seen_frames >= self.min_confirmation_frames:
                    state.is_confirmed = True

                # Update timestamp and centroid
                state.last_centroid = (cx, cy)
                state.last_seen_timestamp = timestamp
                state.last_seen_frame = frame_number
                state.is_alive = True
                state.observation_type = ObservationState.OBSERVED
                state.last_observation_frame_id = frame_number
                state.last_observation_timestamp = timestamp

            if state.is_confirmed:
                self.historical_tracks_count.setdefault(lane_name, set()).add(tid)

            # Enrich Detection object with computed state parameters
            det.motion_px_sec = state.motion_px_sec
            det.time_in_lane_sec = state.time_in_lane_sec
            det.queue_time_sec = state.queue_time_sec
            det.is_priority = state.is_priority

        # Purge stale tracks exceeding inactivity timeout
        self._purge_stale_tracks(current_frame_track_ids, timestamp)

        return detections

    def _purge_stale_tracks(self, active_track_ids: set, current_timestamp: float) -> None:
        """
        Mark tracks as inactive/dead if not seen in current frame.
        Phase 3.5: Uses a grace period (TRACK_REMOVAL_GRACE_SEC) before purging to
        tolerate temporary occlusions and prevent one-frame disappearance flicker.
        Final purge still uses TRACK_EXPIRATION_TIMEOUT_SEC as the hard upper bound.
        """
        stale_ids = []
        for tid, state in self.active_states.items():
            if tid not in active_track_ids:
                inactivity_duration = current_timestamp - state.last_seen_timestamp
                state.is_alive = False
                # Hard purge after full expiration timeout
                if inactivity_duration > TRACK_EXPIRATION_TIMEOUT_SEC:
                    stale_ids.append(tid)
                # Grace-period soft purge: mark unconfirmed after grace period
                elif inactivity_duration > self.track_removal_grace_sec:
                    stale_ids.append(tid)

        for tid in stale_ids:
            del self.active_states[tid]

    def get_active_vehicles_by_lane(self) -> Dict[str, List[VehicleState]]:
        """
        Return list of active (alive) VehicleState instances grouped by lane.
        """
        grouped: Dict[str, List[VehicleState]] = {}
        for state in self.active_states.values():
            if state.is_alive:
                lane = state.lane
                if lane not in grouped:
                    grouped[lane] = []
                grouped[lane].append(state)
        return grouped

    def get_confirmed_vehicles_by_lane(self) -> Dict[str, List[VehicleState]]:
        """
        Phase 3.5: Return only confirmed vehicles (seen >= MIN_CONFIRMATION_FRAMES)
        grouped by lane. Filters out one-frame false positives from scheduling input.
        """
        grouped: Dict[str, List[VehicleState]] = {}
        for state in self.active_states.values():
            if state.is_alive and state.is_confirmed:
                lane = state.lane
                if lane not in grouped:
                    grouped[lane] = []
                grouped[lane].append(state)
        return grouped
