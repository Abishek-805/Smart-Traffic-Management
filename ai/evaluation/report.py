"""Deterministic model evidence reporting by class, scene, size and provenance."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from typing import Any, Iterable, Optional

from ai.evaluation.manifest import EvaluationManifest, FrameAnnotation
from ai.evaluation.model_evaluator import (
    EvaluationPrediction,
    GroundTruthAnnotation,
    ModelEvaluator,
    compute_iou,
)


@dataclass(frozen=True)
class EvidenceMetadata:
    git_commit: str
    configuration: dict
    model_sha256: str
    model_identity: str
    input_size: int
    runtime: str
    warmup_policy: dict
    trial_count: int
    environment: dict
    latency_ms: dict = field(default_factory=dict)
    throughput_fps: Optional[float] = None
    peak_memory_mb: Optional[float] = None


@dataclass(frozen=True)
class ReportClassMetric:
    ground_truths: int
    predictions: int
    precision: Optional[float]
    recall: Optional[float]
    ap50: Optional[float]
    ap50_95: Optional[float]


@dataclass(frozen=True)
class SliceMetric:
    frames: int
    ground_truths: int
    predictions: int
    precision: Optional[float]
    recall: Optional[float]
    count_mae: Optional[float]


@dataclass
class EvaluationReport:
    metadata: EvidenceMetadata
    total_frames: int
    total_ground_truths: int
    total_predictions: int
    total_false_positives: int
    total_false_negatives: int
    ignored_predictions: int
    map50: Optional[float]
    map50_95: Optional[float]
    count_mae: Optional[float]
    per_class: dict[str, ReportClassMetric] = field(default_factory=dict)
    scene_metrics: dict[str, SliceMetric] = field(default_factory=dict)
    size_metrics: dict[str, SliceMetric] = field(default_factory=dict)
    provenance_metrics: dict[str, SliceMetric] = field(default_factory=dict)
    false_positive_examples: list[dict[str, Any]] = field(default_factory=list)
    false_negative_examples: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def evaluate(
        cls,
        manifest: EvaluationManifest,
        predictions: Iterable[EvaluationPrediction],
        metadata: EvidenceMetadata,
        target_classes: Iterable[str] = (),
        max_error_examples: int = 25,
    ) -> "EvaluationReport":
        frames = {frame.frame_id: frame for frame in manifest.frames}
        raw_predictions = [item for item in predictions if item.image_id in frames]
        kept_predictions = []
        ignored = 0
        for prediction in raw_predictions:
            frame = frames[prediction.image_id]
            if any(_box_center_in_polygon(prediction.bbox, polygon) for polygon in frame.ignore_regions):
                ignored += 1
            else:
                kept_predictions.append(prediction)

        ground_truths = _ground_truths(manifest.frames)
        metrics = ModelEvaluator().evaluate(kept_predictions, ground_truths)
        classes = sorted(set(target_classes) | {item.class_name for item in ground_truths} | {item.class_name for item in kept_predictions})
        per_class = {}
        for name in classes:
            gts = [item for item in ground_truths if item.class_name == name]
            preds = [item for item in kept_predictions if item.class_name == name]
            measured = metrics.per_class.get(name)
            per_class[name] = ReportClassMetric(
                ground_truths=len(gts),
                predictions=len(preds),
                precision=measured.precision if measured and preds else (0.0 if preds else None),
                recall=measured.recall if measured and gts else None,
                ap50=measured.ap50 if measured and gts else None,
                ap50_95=measured.ap50_95 if measured and gts else None,
            )

        scene_metrics = {
            tag: _slice_metric(
                [frame for frame in manifest.frames if tag in frame.scene_tags], kept_predictions
            )
            for tag in sorted({tag for frame in manifest.frames for tag in frame.scene_tags})
        }
        size_metrics = {
            size: _size_slice(size, manifest.frames, kept_predictions)
            for size in ("small", "medium", "large")
        }
        provenance_metrics = {}
        for provenance, datasets in manifest.datasets_by_provenance().items():
            ids = {item.dataset_id for item in datasets}
            provenance_metrics[provenance] = _slice_metric(
                [frame for frame in manifest.frames if frame.dataset_id in ids], kept_predictions
            )

        false_positives, false_negatives = _error_examples(
            ground_truths, kept_predictions, max(0, max_error_examples)
        )
        has_ground_truth = bool(ground_truths)
        return cls(
            metadata=metadata,
            total_frames=len(manifest.frames),
            total_ground_truths=len(ground_truths),
            total_predictions=len(kept_predictions),
            total_false_positives=metrics.total_false_positives,
            total_false_negatives=metrics.total_false_negatives,
            ignored_predictions=ignored,
            map50=metrics.map50 if has_ground_truth else None,
            map50_95=metrics.map50_95 if has_ground_truth else None,
            count_mae=metrics.count_mae if manifest.frames else None,
            per_class=per_class,
            scene_metrics=scene_metrics,
            size_metrics=size_metrics,
            provenance_metrics=provenance_metrics,
            false_positive_examples=false_positives,
            false_negative_examples=false_negatives,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": asdict(self.metadata),
            "summary": {
                "total_frames": self.total_frames,
                "total_ground_truths": self.total_ground_truths,
                "total_predictions": self.total_predictions,
                "total_false_positives": self.total_false_positives,
                "total_false_negatives": self.total_false_negatives,
                "ignored_predictions": self.ignored_predictions,
                "map50": self.map50,
                "map50_95": self.map50_95,
                "count_mae": self.count_mae,
            },
            "per_class": {key: asdict(self.per_class[key]) for key in sorted(self.per_class)},
            "scene_metrics": {key: asdict(self.scene_metrics[key]) for key in sorted(self.scene_metrics)},
            "size_metrics": {key: asdict(self.size_metrics[key]) for key in sorted(self.size_metrics)},
            "provenance_metrics": {key: asdict(self.provenance_metrics[key]) for key in sorted(self.provenance_metrics)},
            "false_positive_examples": sorted(self.false_positive_examples, key=_example_key),
            "false_negative_examples": sorted(self.false_negative_examples, key=_example_key),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, allow_nan=False)


def _ground_truths(frames: Iterable[FrameAnnotation]) -> list[GroundTruthAnnotation]:
    return [
        GroundTruthAnnotation(
            image_id=frame.frame_id,
            class_id=item.class_id,
            class_name=item.class_name,
            bbox=tuple(round(value) for value in item.bbox),
        )
        for frame in frames
        for item in frame.annotations
    ]


def _slice_metric(frames: list[FrameAnnotation], predictions: list[EvaluationPrediction]) -> SliceMetric:
    frame_ids = {frame.frame_id for frame in frames}
    gts = _ground_truths(frames)
    preds = [item for item in predictions if item.image_id in frame_ids]
    if not frames:
        return SliceMetric(0, 0, 0, None, None, None)
    metrics = ModelEvaluator().evaluate(preds, gts)
    return SliceMetric(
        frames=len(frames),
        ground_truths=len(gts),
        predictions=len(preds),
        precision=metrics.overall_precision if preds else None,
        recall=metrics.overall_recall if gts else None,
        count_mae=metrics.count_mae,
    )


def _size_name(bbox) -> str:
    area = max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])
    return "small" if area < 32**2 else "medium" if area < 96**2 else "large"


def _size_slice(size: str, frames: tuple[FrameAnnotation, ...], predictions: list[EvaluationPrediction]) -> SliceMetric:
    ground_truths = [
        GroundTruthAnnotation(frame.frame_id, item.class_id, item.class_name,
                              tuple(round(value) for value in item.bbox))
        for frame in frames for item in frame.annotations if _size_name(item.bbox) == size
    ]
    selected_predictions = [item for item in predictions if _size_name(item.bbox) == size]
    frame_ids = {item.image_id for item in ground_truths} | {item.image_id for item in selected_predictions}
    if not frame_ids:
        return SliceMetric(0, 0, 0, None, None, None)
    metrics = ModelEvaluator().evaluate(selected_predictions, ground_truths)
    return SliceMetric(
        frames=len(frame_ids), ground_truths=len(ground_truths), predictions=len(selected_predictions),
        precision=metrics.overall_precision if selected_predictions else None,
        recall=metrics.overall_recall if ground_truths else None,
        count_mae=metrics.count_mae,
    )


def _box_center_in_polygon(bbox, polygon) -> bool:
    x = (bbox[0] + bbox[2]) / 2.0
    y = (bbox[1] + bbox[3]) / 2.0
    inside = False
    previous = polygon[-1]
    for current in polygon:
        x1, y1 = previous
        x2, y2 = current
        if (y1 > y) != (y2 > y):
            crossing_x = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < crossing_x:
                inside = not inside
        previous = current
    return inside


def _error_examples(ground_truths, predictions, limit):
    matched_gt = set()
    false_positives = []
    ordered_predictions = sorted(predictions, key=lambda item: (-item.confidence, item.image_id, item.class_name))
    for prediction in ordered_predictions:
        candidates = [
            (index, gt, compute_iou(prediction.bbox, gt.bbox))
            for index, gt in enumerate(ground_truths)
            if index not in matched_gt and gt.image_id == prediction.image_id and gt.class_name == prediction.class_name
        ]
        best = max(candidates, key=lambda item: item[2], default=None)
        if best and best[2] >= 0.5:
            matched_gt.add(best[0])
        else:
            false_positives.append({
                "frame_id": prediction.image_id, "class_name": prediction.class_name,
                "bbox": list(prediction.bbox), "confidence": prediction.confidence,
            })
    false_negatives = [
        {"frame_id": gt.image_id, "class_name": gt.class_name, "bbox": list(gt.bbox)}
        for index, gt in enumerate(ground_truths) if index not in matched_gt
    ]
    return sorted(false_positives, key=_example_key)[:limit], sorted(false_negatives, key=_example_key)[:limit]


def _example_key(item):
    return (item["frame_id"], item["class_name"], tuple(item["bbox"]))
