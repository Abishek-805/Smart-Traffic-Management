"""
Traffic, vehicle class mappings, lane ROI configurations, and congestion scoring parameters.
Runtime class selection is model-name based. This supports both COCO pretrained
weights and the 14-class UVH-26 Indian traffic taxonomy.
"""

from typing import Dict, Any

TARGET_CLASS_NAMES = {
    "bicycle", "car", "motorcycle", "bus", "truck",
    "hatchback", "sedan", "suv", "muv", "three-wheeler", "two-wheeler",
    "lcv", "mini-bus", "tempo-traveller", "van", "other",
}


def normalize_vehicle_class(value: str) -> str:
    """Normalize COCO/UVH label spelling without collapsing useful subclasses."""
    normalized = str(value).strip().lower().replace("_", "-").replace(" ", "-")
    return {
        "2-wheeler": "two-wheeler",
        "3-wheeler": "three-wheeler",
        "minibus": "mini-bus",
        "tempo-traveler": "tempo-traveller",
    }.get(normalized, normalized)

# PCE (Passenger Car Equivalent) space occupancy weights
PCE_WEIGHTS = {
    "car": 1.0,
    "bus": 1.5,
    "truck": 2.0,
    "motorcycle": 0.5,
    "bicycle": 0.5,
    "two-wheeler": 0.5,
    "three-wheeler": 0.8,
    "hatchback": 1.0,
    "sedan": 1.0,
    "suv": 1.2,
    "muv": 1.2,
    "van": 1.2,
    "lcv": 1.5,
    "tempo-traveller": 1.5,
    "mini-bus": 2.0,
    "other": 1.0,
}

# Motion and queue detection parameters
QUEUE_MOTION_THRESHOLD_PX_SEC = 15.0  # Motion below 15 px/s is low speed
CONSECUTIVE_QUEUE_FRAMES = 10         # Vehicle must be slow for 10 frames to be marked queued
# ── Phase 3.5 — Vehicle Count Stabilization ──────────────────────────────────
EMA_ALPHA = 0.4                       # Exponential Moving Average smoothing factor (0–1)
COUNT_HISTORY_SIZE = 10               # Rolling window size for raw count history
MIN_CONFIRMATION_FRAMES = 2           # Minimum frames a track must exist before counting
TRACK_REMOVAL_GRACE_SEC = 1.8         # Measured grace period before purging a lost track (frame arrival jitter tolerance)
TRACK_EXPIRATION_TIMEOUT_SEC = 4.0    # Hard purge stale tracks after 4 seconds of inactivity
LANE_SWITCH_CONFIRMATION_FRAMES = 3  # Observed frames required before committing a lane transition

# Configurable congestion scoring weights
CONGESTION_WEIGHTS = {
    "pce": 1.0,
    "queue_time": 0.2,
    "stopped": 5.0,
}

# Density level score thresholds
DENSITY_THRESHOLDS = {
    "LOW": 8.0,
    "MEDIUM": 18.0,
    "HIGH": 30.0,
    # Anything above HIGH is "CONGESTED"
}
