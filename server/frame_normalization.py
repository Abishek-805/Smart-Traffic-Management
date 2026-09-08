"""Canonical frame orientation handling for camera protocol images."""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np


VALID_ROTATIONS = (0, 90, 180, 270)


def parse_rotation(value: Any) -> int:
    """Return a validated clockwise correction in degrees."""
    if value is None:
        return 0
    if isinstance(value, bool):
        raise ValueError("rotation must be one of 0, 90, 180 or 270")
    try:
        rotation = int(value) % 360
    except (TypeError, ValueError) as exc:
        raise ValueError("rotation must be one of 0, 90, 180 or 270") from exc
    if rotation not in VALID_ROTATIONS:
        raise ValueError("rotation must be one of 0, 90, 180 or 270")
    return rotation


def normalize_frame_orientation(frame: np.ndarray, rotation: Any = 0):
    """Apply the protocol's clockwise rotation exactly once before inference."""
    if not isinstance(frame, np.ndarray) or frame.ndim not in (2, 3):
        raise ValueError("frame must be a decoded image array")
    correction = parse_rotation(rotation)
    if correction == 90:
        normalized = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    elif correction == 180:
        normalized = cv2.rotate(frame, cv2.ROTATE_180)
    elif correction == 270:
        normalized = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    else:
        normalized = frame
    return normalized, {
        "rotation": correction,
        "input_width": int(frame.shape[1]),
        "input_height": int(frame.shape[0]),
        "width": int(normalized.shape[1]),
        "height": int(normalized.shape[0]),
    }
