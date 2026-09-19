from pathlib import Path

from ai.evaluation.manifest import EvaluationManifest
from ai.evaluation.model_evaluator import EvaluationPrediction
from ai.evaluation.report import EvidenceMetadata, EvaluationReport


FIXTURE = Path(__file__).parent / "fixtures" / "evaluation" / "sample-manifest.json"


def metadata() -> EvidenceMetadata:
    return EvidenceMetadata(
        git_commit="abc1234",
        configuration={"confidence": 0.25},
        model_sha256="0" * 64,
        model_identity="fixture-detector",
        input_size=640,
        runtime="pytest",
        warmup_policy={"iterations": 1},
        trial_count=1,
        environment={"device": "cpu"},
    )


def prediction(frame_id, class_id, class_name, bbox, confidence=0.9):
    return EvaluationPrediction(frame_id, class_id, class_name, bbox, confidence)


def test_report_separates_night_small_objects_and_provenance():
    manifest = EvaluationManifest.load(FIXTURE)
    predictions = [
        prediction("external-day-001", 2, "car", (100, 200, 260, 340)),
        prediction("project-night-001", 5, "three-wheeler", (600, 400, 760, 650)),
    ]

    report = EvaluationReport.evaluate(
        manifest, predictions, metadata(), target_classes=("car", "three-wheeler", "truck")
    )

    assert report.scene_metrics["night"].frames == 1
    assert report.scene_metrics["night"].ground_truths == 1
    assert report.size_metrics["large"].ground_truths == 2
    assert set(report.provenance_metrics) == {"external", "project_owned"}


def test_prediction_inside_ignore_region_is_not_false_positive():
    manifest = EvaluationManifest.load(FIXTURE)
    ignored_prediction = prediction("project-night-001", 2, "car", (10, 10, 80, 80))

    report = EvaluationReport.evaluate(manifest, [ignored_prediction], metadata())

    assert report.total_false_positives == 0
    assert report.ignored_predictions == 1


def test_absent_class_metric_is_unavailable():
    manifest = EvaluationManifest.load(FIXTURE)

    report = EvaluationReport.evaluate(
        manifest, [], metadata(), target_classes=("car", "three-wheeler", "truck")
    )

    assert report.per_class["truck"].ap50 is None
    assert report.per_class["truck"].recall is None


def test_serialization_is_deterministic_and_caps_examples():
    manifest = EvaluationManifest.load(FIXTURE)
    predictions = [
        prediction("external-day-001", 2, "car", (0, 0, 20, 20), confidence=0.7),
        prediction("external-day-001", 2, "car", (20, 20, 40, 40), confidence=0.6),
    ]

    report = EvaluationReport.evaluate(
        manifest, predictions, metadata(), max_error_examples=1
    )
    first = report.to_json()
    second = report.to_json()

    assert first == second
    assert len(report.false_positive_examples) == 1
    assert report.total_false_positives == 2
