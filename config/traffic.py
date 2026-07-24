"""
Traffic, vehicle class mappings, lane ROI configurations, and congestion scoring parameters.
COCO Class Index Mapping:
2: car
3: motorcycle
5: bus
7: truck
"""

from typing import Dict, Any

VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

# Target class sets for fast lookups
TARGET_CLASS_IDS = set(VEHICLE_CLASSES.keys())
TARGET_CLASS_NAMES = set(VEHICLE_CLASSES.values())

# PCE (Passenger Car Equivalent) space occupancy weights
PCE_WEIGHTS = {
    "car": 1.0,
    "bus": 1.5,
    "truck": 2.0,
    "motorcycle": 0.5,
}

# Motion and queue detection parameters
QUEUE_MOTION_THRESHOLD_PX_SEC = 15.0  # Motion below 15 px/s is low speed
CONSECUTIVE_QUEUE_FRAMES = 10         # Vehicle must be slow for 10 frames to be marked queued
TRACK_EXPIRATION_TIMEOUT_SEC = 3.0    # Purge stale tracks after 3 seconds of inactivity

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
