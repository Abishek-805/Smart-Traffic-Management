"""Fail-closed acceptance gate for model and perception evidence reports."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any


@dataclass(frozen=True)
class QualityGatePolicy:
    maximum_map50_95_drop: float = 0.0
    maximum_per_class_recall_drop: float = 0.0
    maximum_count_mae_increase: float = 0.0
    maximum_id_switch_increase: int = 0
    required_latency_improvement_fraction: float = 0.0

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "QualityGatePolicy":
        expected = set(cls.__dataclass_fields__)
        if set(value) != expected:
            raise ValueError(f"Quality gate policy keys must be exactly: {sorted(expected)}")
        policy = cls(**value)
        if any(getattr(policy, key) < 0 for key in expected):
            raise ValueError("Quality gate allowances must be non-negative")
        if policy.required_latency_improvement_fraction >= 1:
            raise ValueError("required_latency_improvement_fraction must be below 1")
        return policy


@dataclass(frozen=True)
class GateResult:
    accepted: bool
    failures: dict[str, str] = field(default_factory=dict)


def compare_reports(baseline: dict, candidate: dict, policy: QualityGatePolicy) -> GateResult:
    failures: dict[str, str] = {}
    baseline_summary = baseline.get("summary", {})
    candidate_summary = candidate.get("summary", {})

    _maximum_drop(
        failures, "map50_95", baseline_summary.get("map50_95"),
        candidate_summary.get("map50_95"), policy.maximum_map50_95_drop,
    )
    _maximum_increase(
        failures, "count_mae", baseline_summary.get("count_mae"),
        candidate_summary.get("count_mae"), policy.maximum_count_mae_increase,
    )
    _maximum_increase(
        failures, "id_switches", baseline_summary.get("id_switches"),
        candidate_summary.get("id_switches"), policy.maximum_id_switch_increase,
    )

    baseline_classes = baseline.get("per_class", {})
    candidate_classes = candidate.get("per_class", {})
    for class_name in sorted(baseline_classes):
        baseline_recall = baseline_classes[class_name].get("recall")
        if baseline_recall is None:
            continue
        candidate_recall = candidate_classes.get(class_name, {}).get("recall")
        _maximum_drop(
            failures, f"recall:{class_name}", baseline_recall, candidate_recall,
            policy.maximum_per_class_recall_drop,
        )

    baseline_p95 = baseline.get("metadata", {}).get("latency_ms", {}).get("p95")
    candidate_p95 = candidate.get("metadata", {}).get("latency_ms", {}).get("p95")
    if not _number(baseline_p95) or not _number(candidate_p95):
        failures["latency_p95"] = "baseline and candidate p95 latency are required"
    else:
        maximum = baseline_p95 * (1.0 - policy.required_latency_improvement_fraction)
        if candidate_p95 > maximum + 1e-12:
            failures["latency_p95"] = f"candidate {candidate_p95} exceeds allowed {maximum}"

    return GateResult(accepted=not failures, failures=failures)


def _maximum_drop(failures, name, baseline, candidate, allowance):
    if not _number(baseline) or not _number(candidate):
        failures[name] = "baseline and candidate values are required"
    elif baseline - candidate > allowance + 1e-12:
        failures[name] = f"drop {baseline - candidate:.6f} exceeds {allowance:.6f}"


def _maximum_increase(failures, name, baseline, candidate, allowance):
    if not _number(baseline) or not _number(candidate):
        failures[name] = "baseline and candidate values are required"
    elif candidate - baseline > allowance + 1e-12:
        failures[name] = f"increase {candidate - baseline:.6f} exceeds {allowance:.6f}"


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
