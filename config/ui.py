"""
UI rendering and visualization theme configurations.
"""

WINDOW_NAME = "Smart Traffic Management System - Sprint 1"

# Modern BGR color palettes for OpenCV visualization
CLASS_COLORS = {
    "car": (0, 215, 255),       # Bright Yellow/Gold
    "motorcycle": (255, 144, 30), # Vibrant Cyan/Blue
    "bus": (50, 205, 50),       # Lime Green
    "truck": (255, 69, 0),      # Vivid Red/Orange
}

DEFAULT_COLOR = (200, 200, 200) # Soft Gray fallback

# Rendering line thickness and font metrics
BOX_THICKNESS = 2
FONT_SCALE = 0.55
FONT_THICKNESS = 2
TEXT_COLOR = (255, 255, 255)

# HUD overlay aesthetics
HUD_BG_COLOR = (15, 15, 15)     # Sleek Dark Slate
HUD_TEXT_COLOR = (0, 255, 204)  # Neon Mint
