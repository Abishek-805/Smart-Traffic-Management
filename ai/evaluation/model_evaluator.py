"""
Reusable Model Evaluation Lab for measuring object detection accuracy, tracking error,
and traffic vehicle count accuracy against labelled ground-truth datasets.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np


def compute_iou(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
    """
    Compute Intersection-over-Union (IoU) between two bounding boxes [x1, y1, x2, y2].
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection_area = max(0, x2 - x1) * max(0, y2 - y1)
    box1_area = max(0, box1[2] - box1[0]) * max(0, box1[3] - box1[1])
    box2_area = max(0, box2[2] - box2[0]) * max(0, box2[3] - box2[1])

    union_area = box1_area + box2_area - intersection_area
    if union_area <= 0:
        return 0.0
    return float(intersection_area / union_area)


@dataclass(frozen=True)
class GroundTruthAnnotation:
    """Labelled ground-truth vehicle annotation."""
    image_id: str
    class_id: int
    class_name: str
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    is_crowd: bool = False


@dataclass(frozen=True)
class EvaluationPrediction:
    """Model detection prediction to be evaluated."""
    image_id: str
    class_id: int
    class_name: str
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float


@dataclass
class ClassMetrics:
    """Performance metrics for one vehicle class."""
    class_name: str
    class_id: int
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    ap50: float = 0.0
    ap50_95: float = 0.0


@dataclass
class EvaluationMetrics:
    """Consolidated metrics across all evaluated classes and images."""
    total_images: int
    total_ground_truths: int
    total_predictions: int
    total_true_positives: int
    total_false_positives: int
    total_false_negatives: int
    overall_precision: float
    overall_recall: float
    overall_f1: float
    map50: float
    map50_95: float
    count_mae: float
    count_rmse: float
    per_class: Dict[str, ClassMetrics] = field(default_factory=dict)
    confusion_matrix: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_images": self.total_images,
            "total_ground_truths": self.total_ground_truths,
            "total_predictions": self.total_predictions,
            "overall_precision": round(self.overall_precision, 4),
            "overall_recall": round(self.overall_recall, 4),
            "overall_f1": round(self.overall_f1, 4),
            "map50": round(self.map50, 4),
            "map50_95": round(self.map50_95, 4),
            "count_mae": round(self.count_mae, 4),
            "count_rmse": round(self.count_rmse, 4),
            "per_class": {
                name: {
                    "precision": round(m.precision, 4),
                    "recall": round(m.recall, 4),
                    "f1_score": round(m.f1_score, 4),
                    "ap50": round(m.ap50, 4),
                    "ap50_95": round(m.ap50_95, 4),
                    "tp": m.true_positives,
                    "fp": m.false_positives,
                    "fn": m.false_negatives,
                }
                for name, m in self.per_class.items()
            },
            "confusion_matrix": self.confusion_matrix,
        }

    def to_markdown(self) -> str:
        lines = [
            "# Model Evaluation Summary Report",
            "",
            f"- **Images Evaluated**: {self.total_images}",
            f"- **Ground Truth Objects**: {self.total_ground_truths}",
            f"- **Model Predictions**: {self.total_predictions}",
            f"- **Overall Precision**: {self.overall_precision * 100:.2f}%",
            f"- **Overall Recall**: {self.overall_recall * 100:.2f}%",
            f"- **Overall F1-Score**: {self.overall_f1 * 100:.2f}%",
            f"- **mAP@50**: {self.map50 * 100:.2f}%",
            f"- **mAP@50:95**: {self.map50_95 * 100:.2f}%",
            f"- **Vehicle Count MAE**: {self.count_mae:.2f} vehicles/frame",
            f"- **Vehicle Count RMSE**: {self.count_rmse:.2f} vehicles/frame",
            "",
            "## Per-Class Performance",
            "",
            "| Class | TP | FP | FN | Precision | Recall | F1 | AP@50 | AP@50:95 |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for name, m in sorted(self.per_class.items()):
            lines.append(
                f"| {name} | {m.true_positives} | {m.false_positives} | {m.false_negatives} | "
                f"{m.precision * 100:.1f}% | {m.recall * 100:.1f}% | {m.f1_score * 100:.1f}% | "
                f"{m.ap50 * 100:.1f}% | {m.ap50_95 * 100:.1f}% |"
            )
        return "\n".join(lines)


class DatasetLoader:
    """Loads ground-truth dataset annotations from standard formats."""

    @staticmethod
    def load_coco_json(coco_path: str | Path) -> List[GroundTruthAnnotation]:
        """Parse standard COCO JSON format annotations."""
        path = Path(coco_path)
        if not path.exists():
            raise FileNotFoundError(f"COCO annotation file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        categories = {c["id"]: c["name"] for c in data.get("categories", [])}
        images = {img["id"]: str(img.get("file_name", img["id"])) for img in data.get("images", [])}

        annotations = []
        for ann in data.get("annotations", []):
            cat_id = ann["category_id"]
            img_id = images.get(ann["image_id"], str(ann["image_id"]))
            bbox = ann["bbox"]  # [x, y, width, height]
            x1 = int(round(bbox[0]))
            y1 = int(round(bbox[1]))
            x2 = int(round(bbox[0] + bbox[2]))
            y2 = int(round(bbox[1] + bbox[3]))
            annotations.append(
                GroundTruthAnnotation(
                    image_id=img_id,
                    class_id=cat_id,
                    class_name=categories.get(cat_id, str(cat_id)),
                    bbox=(x1, y1, x2, y2),
                    is_crowd=bool(ann.get("iscrowd", 0)),
                )
            )
        return annotations

    @staticmethod
    def load_yolo_txt(
        annotation_file: str | Path,
        image_id: str,
        image_width: int,
        image_height: int,
        class_mapping: Optional[Dict[int, str]] = None,
    ) -> List[GroundTruthAnnotation]:
        """Parse YOLO normalized format text file: `class_id x_center y_center width height`."""
        path = Path(annotation_file)
        if not path.exists():
            return []

        annotations = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 5:
                    continue
                cls_id = int(parts[0])
                xc = float(parts[1]) * image_width
                yc = float(parts[2]) * image_height
                w = float(parts[3]) * image_width
                h = float(parts[4]) * image_height
                x1 = int(round(xc - w / 2))
                y1 = int(round(yc - h / 2))
                x2 = int(round(xc + w / 2))
                y2 = int(round(yc + h / 2))
                class_name = class_mapping.get(cls_id, str(cls_id)) if class_mapping else str(cls_id)
                annotations.append(
                    GroundTruthAnnotation(
                        image_id=image_id,
                        class_id=cls_id,
                        class_name=class_name,
                        bbox=(x1, y1, x2, y2),
                    )
                )
        return annotations


class ModelEvaluator:
    """Evaluates prediction lists against ground truth annotations."""

    def __init__(self, iou_thresholds: Optional[List[float]] = None):
        self.iou_thresholds = iou_thresholds or [round(x, 2) for x in np.arange(0.50, 1.00, 0.05)]

    def evaluate(
        self,
        predictions: List[EvaluationPrediction],
        ground_truths: List[GroundTruthAnnotation],
        primary_iou: float = 0.50,
    ) -> EvaluationMetrics:
        """
        Evaluate full dataset predictions against ground truth annotations.
        """
        # Index annotations by image_id
        gt_by_image: Dict[str, List[GroundTruthAnnotation]] = {}
        for gt in ground_truths:
            gt_by_image.setdefault(gt.image_id, []).append(gt)

        pred_by_image: Dict[str, List[EvaluationPrediction]] = {}
        for p in predictions:
            pred_by_image.setdefault(p.image_id, []).append(p)

        all_image_ids = set(gt_by_image.keys()) | set(pred_by_image.keys())
        all_classes: Set[str] = {gt.class_name for gt in ground_truths} | {p.class_name for p in predictions}

        # Initialize confusion matrix
        confusion: Dict[str, Dict[str, int]] = {
            c: {k: 0 for k in sorted(all_classes) + ["background"]} for c in sorted(all_classes) + ["background"]
        }

        # Per-class AP accumulator across IoU thresholds
        class_ap_curves: Dict[str, Dict[float, float]] = {c: {} for c in all_classes}

        # Match at primary IoU threshold (0.50)
        tp_by_class: Dict[str, int] = {c: 0 for c in all_classes}
        fp_by_class: Dict[str, int] = {c: 0 for c in all_classes}
        fn_by_class: Dict[str, int] = {c: 0 for c in all_classes}

        for image_id in all_image_ids:
            img_gts = gt_by_image.get(image_id, [])
            img_preds = sorted(pred_by_image.get(image_id, []), key=lambda x: x.confidence, reverse=True)

            matched_gts: Set[int] = set()

            for pred in img_preds:
                best_iou = 0.0
                best_gt_idx = -1

                for idx, gt in enumerate(img_gts):
                    if idx in matched_gts or gt.class_name != pred.class_name:
                        continue
                    iou = compute_iou(pred.bbox, gt.bbox)
                    if iou > best_iou:
                        best_iou = iou
                        best_gt_idx = idx

                if best_iou >= primary_iou and best_gt_idx >= 0:
                    matched_gts.add(best_gt_idx)
                    tp_by_class[pred.class_name] += 1
                    confusion[pred.class_name][pred.class_name] += 1
                else:
                    fp_by_class[pred.class_name] += 1
                    confusion["background"][pred.class_name] += 1

            for idx, gt in enumerate(img_gts):
                if idx not in matched_gts:
                    fn_by_class[gt.class_name] += 1
                    confusion[gt.class_name]["background"] += 1

        # Calculate AP across multiple IoU thresholds for mAP@50:95
        for cls_name in all_classes:
            cls_preds = sorted([p for p in predictions if p.class_name == cls_name], key=lambda x: x.confidence, reverse=True)
            cls_gts = [gt for gt in ground_truths if gt.class_name == cls_name]
            n_gt = len(cls_gts)

            if n_gt == 0:
                continue

            for iou_th in self.iou_thresholds:
                ap = self._calculate_average_precision(cls_preds, gt_by_image, cls_name, iou_th, n_gt)
                class_ap_curves[cls_name][iou_th] = ap

        # Build ClassMetrics
        per_class: Dict[str, ClassMetrics] = {}
        for c in sorted(all_classes):
            tp = tp_by_class[c]
            fp = fp_by_class[c]
            fn = fn_by_class[c]
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
            ap50 = class_ap_curves[c].get(0.50, 0.0)
            ap_all = list(class_ap_curves[c].values())
            ap50_95 = float(np.mean(ap_all)) if ap_all else 0.0

            per_class[c] = ClassMetrics(
                class_name=c,
                class_id=0,
                true_positives=tp,
                false_positives=fp,
                false_negatives=fn,
                precision=prec,
                recall=rec,
                f1_score=f1,
                ap50=ap50,
                ap50_95=ap50_95,
            )

        # Count errors per image
        count_errors = []
        for image_id in all_image_ids:
            actual_count = len(gt_by_image.get(image_id, []))
            pred_count = len(pred_by_image.get(image_id, []))
            count_errors.append(abs(actual_count - pred_count))

        mae = float(np.mean(count_errors)) if count_errors else 0.0
        rmse = float(math.sqrt(np.mean([e ** 2 for e in count_errors]))) if count_errors else 0.0

        total_tp = sum(tp_by_class.values())
        total_fp = sum(fp_by_class.values())
        total_fn = sum(fn_by_class.values())

        overall_prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        overall_rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        overall_f1 = (2 * overall_prec * overall_rec) / (overall_prec + overall_rec) if (overall_prec + overall_rec) > 0 else 0.0

        map50 = float(np.mean([m.ap50 for m in per_class.values()])) if per_class else 0.0
        map50_95 = float(np.mean([m.ap50_95 for m in per_class.values()])) if per_class else 0.0

        return EvaluationMetrics(
            total_images=len(all_image_ids),
            total_ground_truths=len(ground_truths),
            total_predictions=len(predictions),
            total_true_positives=total_tp,
            total_false_positives=total_fp,
            total_false_negatives=total_fn,
            overall_precision=overall_prec,
            overall_recall=overall_rec,
            overall_f1=overall_f1,
            map50=map50,
            map50_95=map50_95,
            count_mae=mae,
            count_rmse=rmse,
            per_class=per_class,
            confusion_matrix=confusion,
        )

    def _calculate_average_precision(
        self,
        sorted_preds: List[EvaluationPrediction],
        gt_by_image: Dict[str, List[GroundTruthAnnotation]],
        target_class: str,
        iou_threshold: float,
        total_gt: int,
    ) -> float:
        """Calculate VOC/COCO continuous interpolated Average Precision for one class at IoU threshold."""
        if total_gt == 0 or not sorted_preds:
            return 0.0

        matched_gts_by_img: Dict[str, Set[int]] = {}
        tp = np.zeros(len(sorted_preds))
        fp = np.zeros(len(sorted_preds))

        for i, pred in enumerate(sorted_preds):
            img_gts = [g for g in gt_by_image.get(pred.image_id, []) if g.class_name == target_class]
            matched = matched_gts_by_img.setdefault(pred.image_id, set())

            best_iou = 0.0
            best_idx = -1
            for idx, gt in enumerate(img_gts):
                if idx in matched:
                    continue
                iou = compute_iou(pred.bbox, gt.bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_idx = idx

            if best_iou >= iou_threshold and best_idx >= 0:
                matched.add(best_idx)
                tp[i] = 1.0
            else:
                fp[i] = 1.0

        cum_tp = np.cumsum(tp)
        cum_fp = np.cumsum(fp)
        recalls = cum_tp / total_gt
        precisions = cum_tp / np.maximum(cum_tp + cum_fp, np.finfo(np.float64).eps)

        # Standard COCO 101-point or continuous envelope integration
        mrec = np.concatenate(([0.0], recalls, [1.0]))
        mpre = np.concatenate(([0.0], precisions, [0.0]))
        for j in range(len(mpre) - 1, 0, -1):
            mpre[j - 1] = np.maximum(mpre[j - 1], mpre[j])

        # Integrate area under curve
        indices = np.where(mrec[1:] != mrec[:-1])[0]
        ap = np.sum((mrec[indices + 1] - mrec[indices]) * mpre[indices + 1])
        return float(ap)
