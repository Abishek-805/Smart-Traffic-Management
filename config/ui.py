"""
UI rendering and visual theme configurations.
"""

WINDOW_NAME = "Smart Traffic Management System - Production Pipeline"

# Debug overlay toggle
DEBUG_MODE = True

# Modern BGR color palettes for OpenCV visualization
CLASS_COLORS = {
    "car": (0, 215, 255),         # Bright Gold
    "motorcycle": (255, 144, 30),   # Cyan/Blue
    "bus": (50, 205, 50),         # Lime Green
    "truck": (255, 69, 0),        # Vivid Orange/Red
}

DEFAULT_COLOR = (200, 200, 200)

# Debug Centroid and ROI colors
CENTROID_COLOR = (0, 255, 255)    # Neon Yellow dot
UNASSIGNED_COLOR = (0, 0, 255)    # Bright Red

# Rendering line thickness and font metrics
BOX_THICKNESS = 2
FONT_SCALE = 0.55
FONT_THICKNESS = 2
TEXT_COLOR = (255, 255, 255)

# HUD overlay aesthetics
HUD_BG_COLOR = (15, 15, 15)       # Dark Slate
HUD_TEXT_COLOR = (0, 255, 204)    # Neon Mint
