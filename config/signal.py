"""
Traffic signal decision engine configuration parameters.
"""

# Signal timing bounds (in seconds)
MIN_GREEN_SEC = 10
MAX_GREEN_SEC = 60
YELLOW_SEC = 3
ALL_RED_SEC = 2

# Adaptive-cycle tuning. A green ends early only after consecutive fresh empty
# observations, then still passes through yellow/all-red clearance.
EMPTY_LANE_RELEASE_SEC = 1.0
FULL_GREEN_PCE = 20.0
FULL_GREEN_QUEUE_SEC = 120.0

# Priority scoring weights
PRIORITY_WEIGHTS = {
    "pce": 0.45,
    "queue": 0.35,
    "congestion": 0.20,
}

# Starvation & fairness parameters
FAIRNESS_BONUS_PER_CYCLE = 5.0      # Priority bonus added per waiting cycle
MAX_FAIRNESS_BONUS = 25.0           # Maximum cap on cumulative fairness bonus

# Emergency vehicle parameters
EMERGENCY_BOOST_SCORE = 1000.0      # Override score assigned to emergency vehicles
