"""Allow-listed registry that prevents unvalidated perception claims."""
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple


class UnqualifiedFeatureError(ValueError):
    """Raised when a feature lacks accuracy or resource evidence."""


@dataclass(frozen=True)
class PerceptionFeature:
    name: str
    enabled: bool = False
    evidence_path: Optional[Path] = None
    resource_evidence_path: Optional[Path] = None
    status: str = "disabled"


class PerceptionRegistry:
    VALID_STATUSES = {"disabled", "experimental", "qualified"}

    def __init__(self, feature_names: Iterable[str]):
        self._features = {name: PerceptionFeature(name=name) for name in feature_names}

    def enable(
        self,
        name: str,
        evidence_path,
        resource_evidence_path,
        *,
        qualified: bool = False,
    ) -> PerceptionFeature:
        if name not in self._features:
            raise KeyError(f"Unknown perception feature: {name}")
        accuracy = Path(evidence_path) if evidence_path else None
        resources = Path(resource_evidence_path) if resource_evidence_path else None
        if not accuracy or not resources or not accuracy.is_file() or not resources.is_file():
            raise UnqualifiedFeatureError(
                f"{name} requires existing accuracy and resource evidence files before it can be enabled"
            )
        feature = PerceptionFeature(
            name=name,
            enabled=True,
            evidence_path=accuracy,
            resource_evidence_path=resources,
            status="qualified" if qualified else "experimental",
        )
        self._features[name] = feature
        return feature

    def status(self) -> Tuple[PerceptionFeature, ...]:
        return tuple(self._features.values())
