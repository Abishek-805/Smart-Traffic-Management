# Model Evaluation & Dataset Validation Framework

## 1. Overview

The **Model Evaluation Lab** (`ai/evaluation/model_evaluator.py`) provides an automated, reproducible framework for measuring vehicle detection accuracy, tracking stability, and traffic estimation error against labelled ground-truth road datasets.

Because the core repository does not bundle raw traffic video annotations, **formal detection accuracy on Indian road conditions remains quantitatively classified as `UNVALIDATED`** until tested against labelled ground-truth imagery. This framework eliminates guesswork and provides standardized metrics whenever annotated datasets are ingested.

---

## 2. Evaluation Architecture

```
                   Annotated Ground Truth
               (COCO JSON or YOLO TXT Format)
                              │
                              ▼
                        DatasetLoader
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
        GroundTruthAnnotation      EvaluationPrediction
        (BBoxes, Classes, ImageId)  (BBoxes, Scores, ImageId)
                │                           │
                └─────────────┬─────────────┘
                              ▼
                        ModelEvaluator
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
       IoU Matching      Precision/Recall    Count Error
    (Hungarian/Greedy)   (mAP@50, mAP@50:95)  (MAE, RMSE)
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                      EvaluationMetrics
                   (Markdown & JSON Reports)
```

---

## 3. Metrics Calculated

| Metric | Mathematical Definition | Operational Meaning |
|---|---|---|
| **Precision** | $\frac{\text{TP}}{\text{TP} + \text{FP}}$ | Proportion of detected vehicles that actually exist on the road. Low precision leads to phantom traffic triggers. |
| **Recall** | $\frac{\text{TP}}{\text{TP} + \text{FN}}$ | Proportion of real vehicles successfully detected by the model. Low recall leads to neglected demand and signal starvation. |
| **F1-Score** | $2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$ | Harmonic mean balancing false positives and missed vehicles. |
| **mAP@50** | $\frac{1}{C}\sum_{c=1}^C \text{AP}_{50}(c)$ | Mean Average Precision at IoU $\ge 0.50$ across all vehicle classes. Standard object detection benchmark. |
| **mAP@50:95** | $\frac{1}{C}\sum_{c=1}^C \frac{1}{10}\sum_{\tau=0.50}^{0.95} \text{AP}_{\tau}(c)$ | COCO primary metric measuring spatial box tightness and localization precision. |
| **Vehicle Count MAE** | $\frac{1}{N}\sum_{i=1}^N |y_i - \hat{y}_i|$ | Mean Absolute Error in vehicle count per frame. Direct driver of PCE density accuracy. |
| **Vehicle Count RMSE** | $\sqrt{\frac{1}{N}\sum_{i=1}^N (y_i - \hat{y}_i)^2}$ | Root Mean Square Error penalizing severe vehicle counting deviations. |
| **Confusion Matrix** | $M_{c_1, c_2} = \text{Count}(y=c_1, \hat{y}=c_2)$ | Tracks inter-class misclassifications (e.g. bus misclassified as truck, motorcycle as bicycle, background hallucinations). |

---

## 4. Supported Annotation Formats

Before evaluation, datasets must be registered in the versioned manifest contract at
`schemas/evaluation-manifest.schema.json`. The manifest pins annotation checksums,
license/source metadata, split identity, provenance (`external` or `project_owned`),
and scene tags. Results from external datasets and project-owned intersection data
must remain separate; they must never be combined into a single headline metric.

The repository may contain small synthetic fixtures, but raw datasets, recordings,
and trained experiment outputs remain excluded by `.gitignore`.

Reports preserve per-scene, object-size, vehicle-class, and provenance slices.
Missing classes are reported as unavailable rather than perfect, predictions in
declared ignore regions are excluded from false-positive counts, and evidence
metadata records model identity/hash, runtime configuration, latency, throughput,
memory, warm-up policy, trial count, environment, and source commit.

### A. COCO JSON Format
Standard format used by Roboflow, CVAT, and academic benchmarks:
```json
{
  "images": [{"id": 1, "file_name": "frame_001.jpg", "width": 1280, "height": 720}],
  "categories": [{"id": 2, "name": "car"}, {"id": 5, "name": "bus"}],
  "annotations": [
    {"id": 101, "image_id": 1, "category_id": 2, "bbox": [100, 200, 150, 120], "iscrowd": 0}
  ]
}
```

### B. YOLO Normalized Text Format
One text file per image (`<frame_id>.txt`):
```text
# class_id x_center y_center width height (normalized 0.0–1.0)
2 0.512 0.420 0.120 0.095
5 0.740 0.610 0.220 0.180
```

---

## 5. How to Run an Evaluation

### Programmatic Usage
```python
from ai.evaluation.model_evaluator import DatasetLoader, ModelEvaluator, EvaluationPrediction

# 1. Load ground truth
ground_truths = DatasetLoader.load_coco_json("path/to/annotations.json")

# 2. Run model predictions and wrap into EvaluationPrediction instances
predictions = [
    EvaluationPrediction(
        image_id="frame_001.jpg",
        class_id=2,
        class_name="car",
        bbox=(100, 200, 250, 320),
        confidence=0.88,
    ),
    # ...
]

# 3. Evaluate
evaluator = ModelEvaluator()
metrics = evaluator.evaluate(predictions, ground_truths, primary_iou=0.50)

# 4. Generate Reports
print(metrics.to_markdown())
print(metrics.to_dict())
```

---

## 6. Verification Status

- Automated unit and integration tests: [`tests/test_model_evaluation.py`](file:///C:/Users/ashek/Desktop/smart-traffic-management/tests/test_model_evaluation.py) (5/5 passing).
- Validates IoU calculation, perfect prediction scoring (100% precision/recall), imperfect detection matching, COCO JSON parsing, and YOLO txt parsing.

---

## 7. Experimental Perception Features

Speed estimation, stopped-vehicle detection, lane segmentation, and additional
vehicle classes are disabled by default. Enabling one requires both a labelled
accuracy report and a laptop resource report. It remains `experimental` until
the project's qualification policy is passed.

The registry deliberately does not include emergency-vehicle detection. The
project must not claim ambulance or fire-engine recognition until a dedicated,
representative labelled dataset and validated model are available.
