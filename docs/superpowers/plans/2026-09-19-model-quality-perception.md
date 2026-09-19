# Model Quality and Traffic Perception Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish reproducible model-quality evidence, protect YOLOv8n accuracy with regression gates, and improve tracking/count/queue semantics without enabling unsupported perception claims.

**Architecture:** Extend the existing evaluator and calibration code with a repository-controlled manifest, typed provenance, scene/object-size slices, tracking/count measures, and immutable baseline comparison. Keep experiments behind disabled feature flags and keep external and project-owned evidence separate.

**Tech Stack:** Python/dataclasses/Pydantic, NumPy/OpenCV, Ultralytics YOLOv8n, ByteTrack, pytest, JSON/JSON Schema.

**Spec:** `docs/superpowers/specs/2026-09-19-laptop-first-portable-validation-design.md`

## Global Constraints

- YOLOv8n remains the production baseline until a candidate passes the same immutable split.
- Do not commit large or restricted datasets.
- Do not combine external and project-owned results into one metric.
- Do not call image-space distances metres.
- New perception features are disabled by default and require accuracy plus resource evidence.
- Generic COCO weights are not emergency-vehicle detectors.

## Review Focus

- Missing or changed dataset files must fail checksum validation; Task 1 pins this.
- Images with ignore regions must not create false-positive penalties inside ignored areas; Task 2 pins this.
- Empty-class slices must report unavailable rather than perfect AP; Task 2 pins this.
- Track IDs reused after disappearance must count as switches according to one documented rule; Task 3 pins this.
- Uncalibrated queue output must carry `image_space` units, never metres; Task 4 pins this.

---

### Task 1: Versioned Evaluation Manifest and Annotation Contract

**Files:**
- Create: `ai/evaluation/manifest.py`
- Create: `schemas/evaluation-manifest.schema.json`
- Create: `tests/fixtures/evaluation/sample-manifest.json`
- Create: `tests/fixtures/evaluation/annotations.json`
- Create: `tests/test_evaluation_manifest.py`
- Modify: `.gitignore`
- Modify: `docs/MODEL_EVALUATION.md`

**Interfaces:**
- Produces: `EvaluationManifest.load(path)`, `validate_files(root)`, `datasets_by_provenance()`.
- Produces annotation types `BoundingBoxAnnotation`, `FrameAnnotation`, optional `track_id`, `queue_region`, and `ignore_regions`.

- [ ] **Step 1: Write failing provenance/checksum/schema tests**

```python
def test_manifest_keeps_external_and_project_results_separate(tmp_path):
    manifest = EvaluationManifest.load(FIXTURE_MANIFEST)
    groups = manifest.datasets_by_provenance()
    assert set(groups) == {"external", "project_owned"}

def test_changed_asset_fails_checksum(tmp_path):
    manifest = copy_fixture(tmp_path)
    manifest.asset_path.write_bytes(b"changed")
    with pytest.raises(ChecksumMismatch):
        manifest.validate_files(tmp_path)
```

- [ ] **Step 2: Run test and verify missing manifest types fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_evaluation_manifest.py -q`

- [ ] **Step 3: Implement strict manifest parsing**

```python
@dataclass(frozen=True)
class DatasetDescriptor:
    dataset_id: str
    split: str
    provenance: Literal["external", "project_owned"]
    source: str
    license: str
    annotation_revision: str
    sha256: str
    scene_tags: tuple[str, ...]
```

Reject path traversal, unknown provenance, invalid boxes, duplicate frame IDs, non-finite coordinates, and checksum mismatch.

- [ ] **Step 4: Run schema and existing loader tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_evaluation_manifest.py tests/test_model_evaluation.py -q`

- [ ] **Step 5: Commit**

```powershell
git add ai/evaluation/manifest.py schemas tests/fixtures/evaluation tests/test_evaluation_manifest.py .gitignore docs/MODEL_EVALUATION.md
git commit -m "feat: define versioned model evaluation manifest"
```

### Task 2: Scene, Size, Error, and Provenance Reporting

**Files:**
- Modify: `ai/evaluation/model_evaluator.py`
- Create: `ai/evaluation/report.py`
- Modify: `scripts/evaluate_detector.py`
- Create: `tests/test_evaluation_reporting.py`

**Interfaces:**
- Consumes: `EvaluationManifest` from Task 1.
- Produces: `EvaluationReport` with per-class precision/recall/AP, mAP, false positives/negatives, size/scene slices, count MAE, latency, throughput, memory, runtime/model/input/hardware metadata.

- [ ] **Step 1: Write failing slice and ignore-region tests**

```python
def test_report_separates_night_and_small_objects():
    report = evaluate_fixture("mixed-scenes")
    assert report.scene_metrics["night"].count == 2
    assert report.size_metrics["small"].ground_truths == 1

def test_prediction_inside_ignore_region_is_not_false_positive():
    report = evaluate_with_ignore_region()
    assert report.total_false_positives == 0

def test_absent_class_metric_is_unavailable():
    assert evaluate_without_trucks().per_class["truck"].ap50 is None
```

- [ ] **Step 2: Run tests and confirm reporting gaps**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_evaluation_reporting.py -q`

- [ ] **Step 3: Implement deterministic report serialization**

```python
@dataclass
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
```

Sort all map keys and error examples; cap example lists by configuration while retaining total counts.

- [ ] **Step 4: Run evaluator tests and generate a fixture report**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_model_evaluation.py tests/test_evaluation_reporting.py -q
.\.venv\Scripts\python.exe scripts/evaluate_detector.py --manifest tests/fixtures/evaluation/sample-manifest.json --output docs/benchmarks/model-evaluation-fixture.json
```

- [ ] **Step 5: Commit**

Commit as `feat: report model quality by provenance and scene`.

### Task 3: Immutable Baseline, Tracking, and Count Regression Gates

**Files:**
- Create: `ai/evaluation/regression_gate.py`
- Create: `ai/evaluation/tracking_metrics.py`
- Create: `config/model_quality_gate.json`
- Create: `scripts/compare_model_evidence.py`
- Create: `tests/test_model_quality_gate.py`
- Modify: `tests/test_model_regression.py`

**Interfaces:**
- Produces: `compare_reports(baseline, candidate, policy) -> GateResult`.
- Produces: tracking metrics `id_switches`, `mostly_tracked`, `track_fragmentations`, and count MAE.

- [ ] **Step 1: Write failing regression and ID-switch tests**

```python
def test_faster_candidate_fails_when_accuracy_allowance_is_exceeded():
    result = compare_reports(BASELINE, candidate(map50_95=BASELINE.map50_95-.10, p95_ms=10), policy())
    assert not result.accepted
    assert "map50_95" in result.failures

def test_track_identity_change_counts_one_switch():
    metrics = tracking_metrics(gt=[("vehicle-1", 1), ("vehicle-1", 2)], pred=[("track-7", 1), ("track-8", 2)])
    assert metrics.id_switches == 1
```

- [ ] **Step 2: Run tests and verify missing gate fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_model_quality_gate.py -q`

- [ ] **Step 3: Implement explicit policy keys and failure output**

```json
{
  "maximum_map50_95_drop": 0.0,
  "maximum_per_class_recall_drop": 0.0,
  "maximum_count_mae_increase": 0.0,
  "maximum_id_switch_increase": 0,
  "required_latency_improvement_fraction": 0.0
}
```

The default is deliberately strict: no measured regression is permitted. Any later relaxation requires an explicit reviewed configuration change backed by dataset uncertainty analysis; the fixture gate proves mechanics but does not claim field accuracy.

- [ ] **Step 4: Run all evaluation/model tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_model_evaluation.py tests/test_evaluation_manifest.py tests/test_evaluation_reporting.py tests/test_model_quality_gate.py tests/test_model_regression.py -q`

- [ ] **Step 5: Commit**

Commit as `test: enforce model quality regression policy`.

### Task 4: Tracking/Count Stability and Calibrated Queue Semantics

**Files:**
- Modify: `ai/state/count_stabilizer.py`
- Modify: `ai/analytics/calibration.py`
- Modify: `ai/analytics/analytics_exporter.py`
- Modify: `ai/pipeline/traffic_pipeline.py`
- Create: `tests/test_perception_stability.py`
- Modify: `tests/test_queue_calibration.py`

**Interfaces:**
- Produces queue result `{value, unit: "vehicles" | "image_space" | "metres", calibrated, calibration_id}`.
- Produces count stability evidence without changing confirmed-observation semantics.

- [ ] **Step 1: Write queue-unit and occlusion stability tests**

```python
def test_uncalibrated_queue_never_claims_metres():
    result = manager.estimate_queue("north", points, calibration=None)
    assert result.unit == "image_space"
    assert result.calibrated is False

def test_short_occlusion_does_not_create_new_confirmed_count():
    counts = run_tracking_sequence([VISIBLE, OCCLUDED, VISIBLE])
    assert max(counts) == 1
```

- [ ] **Step 2: Run tests and verify current output contract fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_perception_stability.py tests/test_queue_calibration.py tests/test_observation_semantics.py -q`

- [ ] **Step 3: Add explicit units and calibration identity**

Keep existing numeric compatibility fields while adding structured queue metadata; only calibrated homography results may use `metres`.

- [ ] **Step 4: Measure before accepting tracking changes**

Run the immutable fixture sequence through current and candidate settings; accept settings only through `compare_reports`. If no measured improvement exists, retain current ByteTrack settings and commit only the semantic/unit fixes and evidence.

- [ ] **Step 5: Run perception and scheduler safety regression**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_perception_stability.py tests/test_queue_calibration.py tests/test_observation_semantics.py tests/test_safety_invariants.py tests/test_signal_scheduler.py -q`

- [ ] **Step 6: Commit**

Commit as `fix: make queue calibration and count stability explicit`.

### Task 5: Disabled-by-Default Perception Experiment Registry

**Files:**
- Create: `ai/experiments/perception_registry.py`
- Create: `config/perception_features.py`
- Create: `tests/test_perception_feature_flags.py`
- Modify: `web/routes/api_routes.py`
- Modify: `docs/MODEL_EVALUATION.md`

**Interfaces:**
- Produces: `PerceptionFeature(name, enabled, evidence_path, resource_evidence_path, status)`.
- No experimental implementation becomes part of production pipeline in this task.

- [ ] **Step 1: Write failing default-off and evidence tests**

```python
def test_all_unvalidated_perception_features_are_disabled_by_default():
    flags = load_perception_features({})
    assert not flags.speed_estimation
    assert not flags.stopped_vehicle_detection
    assert not flags.lane_segmentation
    assert not flags.additional_vehicle_classes

def test_enabling_feature_without_evidence_is_rejected():
    with pytest.raises(UnqualifiedFeatureError):
        registry.enable("lane_segmentation", evidence_path=None, resource_evidence_path=None)
```

- [ ] **Step 2: Run test and verify failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_perception_feature_flags.py -q`

- [ ] **Step 3: Implement registry and redacted effective status endpoint**

Return `disabled`, `experimental`, or `qualified`; never describe COCO weights as emergency recognition.

- [ ] **Step 4: Run full phase verification**

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Push-Location web-ui; npm run build; Pop-Location
Push-Location ..\traffic-camera-app; npm test; npm run type-check; Pop-Location
```

- [ ] **Step 5: Commit**

Commit as `feat: gate experimental traffic perception features`.
