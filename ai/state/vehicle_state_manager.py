"""
VehicleStateManager maintains state, motion estimation, time-in-lane, and queue detection across frames.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import time

from ai.detection.detection_types import Detection
from config.traffic import (
    QUEUE_MOTION_THRESHOLD_PX_SEC,
    CONSECUTIVE_QUEUE_FRAMES,
    TRACK_EXPIRATION_TIMEOUT_SEC,
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
    is_queued: bool = False
    is_alive: bool = True
    is_priority: bool = False


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
            current_frame_track_ids.add(tid)
            lane_name = det.lane or "Unknown"

            # Register in historical count set
            if lane_name in self.historical_tracks_count:
                self.historical_tracks_count[lane_name].add(tid)
            else:
                self.historical_tracks_count[lane_name] = {tid}

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
                )
                self.active_states[tid] = state
            else:
                state = self.active_states[tid]
                dt = timestamp - state.last_seen_timestamp
                
                # Check for lane transition
                if state.lane != lane_name:
                    logger.info(f"Vehicle #{tid} switched lane: '{state.lane}' -> '{lane_name}'")
                    state.lane = lane_name
                    state.time_in_lane_sec = 0.0
                    state.queue_time_sec = 0.0
                    state.consecutive_low_motion_frames = 0
                elif dt > 0:
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

                # Update timestamp and centroid
                state.last_centroid = (cx, cy)
                state.last_seen_timestamp = timestamp
                state.last_seen_frame = frame_number
                state.is_alive = True

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
        Mark tracks as inactive/dead if not seen in current frame or exceeding timeout.
        """
        stale_ids = []
        for tid, state in self.active_states.items():
            if tid not in active_track_ids:
                inactivity_duration = current_timestamp - state.last_seen_timestamp
                state.is_alive = False
                if inactivity_duration > TRACK_EXPIRATION_TIMEOUT_SEC:
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
