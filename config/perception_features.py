"""Strict, disabled-by-default switches for unqualified perception features."""
from dataclasses import dataclass
from typing import Mapping, Optional
import os


_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off", ""}


def _boolean(value: Optional[str], variable: str) -> bool:
    normalized = "" if value is None else value.strip().lower()
    if normalized in _TRUE:
        return True
    if normalized in _FALSE:
        return False
    raise ValueError(f"{variable} must be a boolean (true/false, 1/0, yes/no, on/off)")


@dataclass(frozen=True)
class PerceptionFeatureFlags:
    speed_estimation: bool = False
    stopped_vehicle_detection: bool = False
    lane_segmentation: bool = False
    additional_vehicle_classes: bool = False


def load_perception_features(environ: Optional[Mapping[str, str]] = None) -> PerceptionFeatureFlags:
    env = os.environ if environ is None else environ
    return PerceptionFeatureFlags(
        speed_estimation=_boolean(env.get("PERCEPTION_SPEED_ESTIMATION"), "PERCEPTION_SPEED_ESTIMATION"),
        stopped_vehicle_detection=_boolean(
            env.get("PERCEPTION_STOPPED_VEHICLE_DETECTION"),
            "PERCEPTION_STOPPED_VEHICLE_DETECTION",
        ),
        lane_segmentation=_boolean(env.get("PERCEPTION_LANE_SEGMENTATION"), "PERCEPTION_LANE_SEGMENTATION"),
        additional_vehicle_classes=_boolean(
            env.get("PERCEPTION_ADDITIONAL_VEHICLE_CLASSES"),
            "PERCEPTION_ADDITIONAL_VEHICLE_CLASSES",
        ),
    )
