"""
Tests for the Model Evaluation Lab (evaluator, IoU, metrics, and dataset loaders).
"""

import json
import tempfile
from pathlib import Path
import pytest
from ai.evaluation.model_evaluator import (
    compute_iou,
    GroundTruthAnnotation,
    EvaluationPrediction,
    ModelEvaluator,
    DatasetLoader,
)


def test_compute_iou():
    # Exact overlap
    b1 = (10, 10, 50, 50)
    assert compute_iou(b1, b1) == pytest.approx(1.0)

    # Disjoint boxes
    b2 = (100, 100, 150, 150)
    assert compute_iou(b1, b2) == 0.0

    # 50% overlap box
    # Area b1 = 40 * 40 = 1600.
    # b3 = (10, 10, 50, 30): area = 40 * 20 = 800.
    # Intersection = 800. Union = 1600 + 800 - 800 = 1600. IoU = 800 / 1600 = 0.5.
    b3 = (10, 10, 50, 30)
    assert compute_iou(b1, b3) == pytest.approx(0.5)


def test_model_evaluator_perfect_predictions():
    evaluator = ModelEvaluator(iou_thresholds=[0.50, 0.75])

    gts = [
        GroundTruthAnnotation(image_id="img1", class_id=2, class_name="car", bbox=(10, 10, 100, 100)),
        GroundTruthAnnotation(image_id="img1", class_id=5, class_name="bus", bbox=(200, 200, 400, 400)),
        GroundTruthAnnotation(image_id="img2", class_id=2, class_name="car", bbox=(50, 50, 150, 150)),
    ]

    preds = [
        EvaluationPrediction(image_id="img1", class_id=2, class_name="car", bbox=(10, 10, 100, 100), confidence=0.95),
        EvaluationPrediction(image_id="img1", class_id=5, class_name="bus", bbox=(200, 200, 400, 400), confidence=0.90),
        EvaluationPrediction(image_id="img2", class_id=2, class_name="car", bbox=(50, 50, 150, 150), confidence=0.88),
    ]

    metrics = evaluator.evaluate(preds, gts, primary_iou=0.50)

    assert metrics.total_images == 2
    assert metrics.total_ground_truths == 3
    assert metrics.total_predictions == 3
    assert metrics.total_true_positives == 3
    assert metrics.total_false_positives == 0
    assert metrics.total_false_negatives == 0
    assert metrics.overall_precision == pytest.approx(1.0)
    assert metrics.overall_recall == pytest.approx(1.0)
    assert metrics.overall_f1 == pytest.approx(1.0)
    assert metrics.count_mae == 0.0
    assert metrics.count_rmse == 0.0
    assert "car" in metrics.per_class
    assert "bus" in metrics.per_class
    assert metrics.per_class["car"].ap50 == pytest.approx(1.0)

    report_md = metrics.to_markdown()
    assert "Model Evaluation Summary Report" in report_md
    assert "**Overall Precision**: 100.00%" in report_md


def test_model_evaluator_imperfect_detections():
    evaluator = ModelEvaluator(iou_thresholds=[0.50])

    gts = [
        GroundTruthAnnotation(image_id="img1", class_id=2, class_name="car", bbox=(0, 0, 50, 50)),
        GroundTruthAnnotation(image_id="img1", class_id=2, class_name="car", bbox=(100, 100, 150, 150)),
    ]

    preds = [
        # Match for first car
        EvaluationPrediction(image_id="img1", class_id=2, class_name="car", bbox=(0, 0, 50, 50), confidence=0.90),
        # False positive (hallucination)
        EvaluationPrediction(image_id="img1", class_id=2, class_name="car", bbox=(300, 300, 350, 350), confidence=0.80),
    ]
    # Second car in GT is missed (false negative)

    metrics = evaluator.evaluate(preds, gts, primary_iou=0.50)

    assert metrics.total_true_positives == 1
    assert metrics.total_false_positives == 1
    assert metrics.total_false_negatives == 1
    assert metrics.overall_precision == pytest.approx(0.5)
    assert metrics.overall_recall == pytest.approx(0.5)
    assert metrics.overall_f1 == pytest.approx(0.5)

    # Confusion matrix
    assert metrics.confusion_matrix["car"]["car"] == 1
    assert metrics.confusion_matrix["background"]["car"] == 1
    assert metrics.confusion_matrix["car"]["background"] == 1


def test_dataset_loader_yolo_txt():
    with tempfile.TemporaryDirectory() as tmpdir:
        label_file = Path(tmpdir) / "frame_001.txt"
        # class_id xc yc w h
        label_file.write_text("2 0.5 0.5 0.2 0.2\n5 0.8 0.8 0.1 0.1\n", encoding="utf-8")

        mapping = {2: "car", 5: "bus"}
        anns = DatasetLoader.load_yolo_txt(label_file, "frame_001", 1000, 1000, mapping)

        assert len(anns) == 2
        assert anns[0].class_name == "car"
        assert anns[0].bbox == (400, 400, 600, 600)
        assert anns[1].class_name == "bus"
        assert anns[1].bbox == (750, 750, 850, 850)


def test_dataset_loader_coco_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        coco_file = Path(tmpdir) / "annotations.json"
        coco_data = {
            "categories": [{"id": 2, "name": "car"}],
            "images": [{"id": 1, "file_name": "scene.jpg"}],
            "annotations": [
                {"id": 101, "image_id": 1, "category_id": 2, "bbox": [50, 60, 100, 120], "iscrowd": 0}
            ],
        }
        coco_file.write_text(json.dumps(coco_data), encoding="utf-8")

        anns = DatasetLoader.load_coco_json(coco_file)
        assert len(anns) == 1
        assert anns[0].image_id == "scene.jpg"
        assert anns[0].class_name == "car"
        assert anns[0].bbox == (50, 60, 150, 180)
