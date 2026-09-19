from ai.evaluation.regression_gate import QualityGatePolicy, compare_reports
from ai.evaluation.tracking_metrics import tracking_metrics


def report(*, map50_95=0.50, count_mae=0.5, p95_ms=100.0, recalls=None, id_switches=1):
    return {
        "summary": {
            "map50_95": map50_95,
            "count_mae": count_mae,
            "id_switches": id_switches,
        },
        "metadata": {"latency_ms": {"p95": p95_ms}},
        "per_class": {
            name: {"recall": value} for name, value in (recalls or {"car": 0.8}).items()
        },
    }


def strict_policy():
    return QualityGatePolicy(
        maximum_map50_95_drop=0.0,
        maximum_per_class_recall_drop=0.0,
        maximum_count_mae_increase=0.0,
        maximum_id_switch_increase=0,
        required_latency_improvement_fraction=0.0,
    )


def test_faster_candidate_fails_when_accuracy_allowance_is_exceeded():
    baseline = report()
    candidate = report(map50_95=0.40, p95_ms=10.0)

    result = compare_reports(baseline, candidate, strict_policy())

    assert not result.accepted
    assert "map50_95" in result.failures


def test_candidate_fails_on_count_tracking_or_per_class_regression():
    baseline = report(recalls={"car": 0.8, "three-wheeler": 0.7})
    candidate = report(
        count_mae=0.8,
        recalls={"car": 0.8, "three-wheeler": 0.6},
        id_switches=3,
    )

    result = compare_reports(baseline, candidate, strict_policy())

    assert set(result.failures) >= {"count_mae", "id_switches", "recall:three-wheeler"}


def test_missing_required_candidate_metric_fails_closed():
    baseline = report(recalls={"car": 0.8, "truck": 0.6})
    candidate = report(recalls={"car": 0.8})

    result = compare_reports(baseline, candidate, strict_policy())

    assert "recall:truck" in result.failures


def test_equal_candidate_passes_strict_policy():
    baseline = report()

    result = compare_reports(baseline, report(), strict_policy())

    assert result.accepted
    assert result.failures == {}


def test_track_identity_change_counts_one_switch():
    metrics = tracking_metrics(
        gt=[("vehicle-1", 1), ("vehicle-1", 2)],
        pred=[("track-7", 1), ("track-8", 2)],
    )

    assert metrics.id_switches == 1
    assert metrics.mostly_tracked == 1


def test_missing_middle_observation_counts_fragmentation_and_count_error():
    metrics = tracking_metrics(
        gt=[("vehicle-1", 1), ("vehicle-1", 2), ("vehicle-1", 3)],
        pred=[("track-7", 1), ("track-7", 3)],
    )

    assert metrics.track_fragmentations == 1
    assert metrics.count_mae == 1 / 3
