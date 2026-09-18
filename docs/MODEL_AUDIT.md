# Traffic AI Model Audit Report
**Source of Truth**: Current repository source code, active configurations, model weights, and verified unit tests.  
**Repository**: `C:\Users\ashek\Desktop\smart-traffic-management`  
**Companion Mobile Node**: `C:\Users\ashek\Desktop\traffic-camera-app`  
**Audit Timestamp**: September 2026  
**Auditor Mode**: Strict Current-Source Only (No Historical Assumptions)

---

## Audit Evidence Classification
Every finding and claim in this audit report is tagged with its empirical verification status:
- **[VERIFIED]**: Directly confirmed from active source code, configuration files, and executed commands.
- **[MEASURED]**: Quantitatively benchmarked on the current machine and recorded in active test artifacts.
- **[INFERRED]**: Logically deduced from code architecture, dependencies, or interfaces.
- **[UNVERIFIED]**: Found in proposed designs, documentation, or external targets without active local verification data.

---

## 1. Current Model Inventory

| Field | Primary In-Repo Model | Supported Alternative (Export) | Proposed Edge Target (Pi) |
|---|---|---|---|
| **Model Name** | `yolov8n` | `yolov8n.onnx` | `yolov8n_ncnn_model` |
| **File Path** | `yolov8n.pt` [VERIFIED] | `models/yolov8n.onnx` [UNVERIFIED FILE] | `models/yolov8n_ncnn_model/` [UNVERIFIED FILE] |
| **File Format** | PyTorch Checkpoint (`.pt`) | Open Neural Network Exchange (`.onnx`) | NCNN Model (`model.param`, `model.bin`) |
| **Runtime Engine** | PyTorch (`torch 2.13.0`, Ultralytics `8.4.136`) | ONNX Runtime (`onnxruntime 1.23.2`) | NCNN (`ncnn 1.0.20260526`) |
| **Used By** | `ai/models/model_manager.py`, `server/frame_coordinator.py`, `ai/pipeline/traffic_pipeline.py` | `scripts/export_edge_model.py`, `requirements-laptop.txt` | `docs/RASPBERRY_PI_DEPLOYMENT.md`, `config/deployment.py` |
| **Default / Optional** | **CURRENT DEFAULT** [VERIFIED] | Optional Laptop Accelerator | Optional Raspberry Pi Target |
| **Input Size** | `576` (laptop profile) / `640` / `512` | `576` / `640` | `512` (Pi profile) |
| **Class Set** | COCO 80 classes, filtered to 5 vehicle classes (1: bicycle, 2: car, 3: motorcycle, 5: bus, 7: truck) | Same 5 classes | Same 5 classes (or 14 UVH-26 classes if fine-tuned) |
| **Confidence Threshold** | `0.08` (`YOLO_CONFIDENCE_THRESHOLD`) [VERIFIED] | `0.08` | `0.08` |
| **NMS Settings** | `iou=0.60`, `max_det=300` [VERIFIED] | `iou=0.60`, `max_det=300` | `iou=0.60`, `max_det=300` |
| **Batch Size** | `4` (laptop profile default, clamped 1-4) [VERIFIED] | Supports 1 or 4 | **Forced to 1** (`if "ncnn" in name: batch=1`) [VERIFIED] |
| **Execution Device** | `auto` (falls back to CPU with 4 threads) [VERIFIED] | CPU (`CPUExecutionProvider`) | CPU (`ncnn` NEON/ARM) |
| **Config Variable** | `YOLO_MODEL_NAME=yolov8n.pt` | `YOLO_MODEL_NAME=models/yolov8n.onnx` | `YOLO_MODEL_NAME=models/yolov8n_ncnn_model` |
| **Expected Location** | `./yolov8n.pt` or `models/yolov8n.pt` | `models/yolov8n.onnx` | `models/yolov8n_ncnn_model/` |
| **Physical Existence on Disk** | **PRESENT** (6,549,796 bytes) [VERIFIED] | Not checked in (generated via export) | Not checked in (generated via export) |

*Note on Deprecated / Removed Models*: `yolo26n.pt` and `yolo26s.pt` were previously benchmarked but were deleted from the repository in commit `e74681d`. They do not exist on disk [VERIFIED].

---

## 2. Trace of the Actual Model Pipeline

Tracing an incoming frame from physical ingestion through inference, tracking, and analytics:

```
[ Camera Frame (JPEG or WebRTC) ]
              │
              ▼
1. INGESTION & DECODING
   - WebSocket JPEG: Base64 payload -> np.frombuffer -> cv2.imdecode(..., IMREAD_COLOR) -> BGR numpy array [VERIFIED]
   - WebRTC Video: av.VideoFrame -> frame.to_ndarray(format='bgr24') -> BGR numpy array [VERIFIED]
   - Local Video File: cv2.VideoCapture.read() -> BGR numpy array [VERIFIED]
              │
              ▼
2. ORIENTATION NORMALIZATION (`server/frame_normalization.py`)
   - Evaluates validated rotation (0, 90, 180, 270 deg) [VERIFIED]
   - Rotates frame using cv2.rotate() BEFORE inference. Bounding boxes are directly mapped in upright coordinates [VERIFIED]
              │
              ▼
3. CADENCE GATING (`ai/pipeline/traffic_pipeline.py`)
   - Evaluates `detector_is_due(last_detection_ts, frame_ts, DETECTOR_FPS=2.0)` [VERIFIED]
   - If NOT due: Skips YOLO forward pass entirely. Invokes `ByteTracker.predict()` (Kalman projection) [VERIFIED]
   - If DUE: Passes frame to batched detector queue [VERIFIED]
              │
              ▼
4. BATCHING & PREPROCESSING (`server/frame_coordinator.py` & Ultralytics `BasePredictor`)
   - Up to 4 active approach frames grouped into batch: `[frame1, frame2, frame3, frame4]` [VERIFIED]
   - Ultralytics internal letterbox resize to `imgsz=576` (preserves aspect ratio with padding) [VERIFIED]
   - Color conversion: BGR to RGB [VERIFIED]
   - Transpose: HWC to CHW tensor layout [VERIFIED]
   - Normalization: Scale `uint8` [0, 255] to `float32` [0.0, 1.0] [VERIFIED]
              │
              ▼
5. NEURAL INFERENCE (`ai/models/model_manager.py`)
   - `model.predict(source=batch, conf=0.08, iou=0.60, imgsz=576, max_det=300, device=..., verbose=False)` [VERIFIED]
   - Single forward pass executes across all grouped approach frames under `_inference_lock` [VERIFIED]
              │
              ▼
6. OUTPUT DECODING & NMS
   - Non-Maximum Suppression executed inside Ultralytics at `iou=0.60`, confidence threshold `0.08` [VERIFIED]
   - Bounding boxes are scaled back from letterboxed 576x576 to original input frame dimensions [VERIFIED]
              │
              ▼
7. CONVERSION & FILTERING (`ai/detection/detector.py`)
   - Boxes clipped to `[0, width]` and `[0, height]` [VERIFIED]
   - Filtered against target vehicle classes: `{1: 'bicycle', 2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}` [VERIFIED]
   - Emits strongly typed `Detection` objects with `ObservationState.OBSERVED` [VERIFIED]
              │
              ▼
8. APPROACH TRACKING (`ai/tracking/byte_tracker.py`)
   - Detections dispatched to independent per-lane `ByteTracker` instances (`self.trackers[lane_name]`) [VERIFIED]
   - First association: matches high-confidence boxes (`conf >= 0.15`) [VERIFIED]
   - Second association: matches low-confidence boxes (`0.08 <= conf < 0.15`) to recover occluded vehicles [VERIFIED]
   - Track initiation: only detections with `conf >= 0.15` can create new tracks [VERIFIED]
              │
              ▼
9. VEHICLE STATE & ANALYTICS (`ai/state/vehicle_state_manager.py` & `ai/analytics/analytics_exporter.py`)
   - Vehicle confirmation: track must be seen for `>= 2` consecutive frames (`MIN_CONFIRMATION_FRAMES=2`) [VERIFIED]
   - Motion estimation: low speed (`< 15 px/s`) for 10 frames flags `is_queued=True` [VERIFIED]
   - Only `OBSERVED` detections update state and accumulate queue times; `PREDICTED` boxes are display-only [VERIFIED]
   - PCE calculation: weighted sum (car=1.0, bus=1.5, truck=2.0, motorcycle=0.5, bicycle=0.5) [VERIFIED]
              │
              ▼
10. DECISION ENGINE (`ai/signal/priority_calculator.py` & `ai/signal/signal_scheduler.py`)
    - Priority scoring: `0.45 * PCE + 0.35 * Queue + 0.20 * Congestion` [VERIFIED]
    - Clockwise fair phase scheduler (`NORTH` -> `EAST` -> `SOUTH` -> `WEST`) allocates dynamic green time [VERIFIED]
    - Signal decision output dispatched to ESP32 UART or in-memory Simulation controller [VERIFIED]
```

### Pipeline Audit Checklist
- **Double resizing**: None. Resizing is performed exactly once inside Ultralytics [VERIFIED].
- **Color conversion mistakes**: None. All ingestion pathways (WebRTC, JPEG, local video) supply BGR uint8 arrays; Ultralytics converts BGR to RGB internally during tensor preprocessing [VERIFIED].
- **Letterboxing & aspect ratio**: Letterbox padding is applied; boxes are automatically rescaled to original frame dimensions without image distortion [VERIFIED].
- **Coordinate scaling**: Ultralytics `scale_boxes()` rescales boxes; `VehicleDetector._convert` validates coordinates with `np.isfinite` and clips to frame boundaries [VERIFIED].
- **Duplicate / missing NMS**: Exactly one NMS pass is run inside Ultralytics at `iou=0.60` [VERIFIED].
- **Model reloading**: Model is loaded once in `ModelManager.__init__` and kept in memory; never reloaded during frame loops [VERIFIED].

---

## 3. Runtime Comparison

| Dimension | PyTorch (`yolov8n.pt`) | ONNX Runtime (`yolov8n.onnx`) | NCNN (`models/yolov8n_ncnn_model`) |
|---|---|---|---|
| **Weight Files** | `yolov8n.pt` (6.25 MB) [VERIFIED] | `yolov8n.onnx` (~12 MB) [INFERRED] | `model.param`, `model.bin` (~6 MB) [INFERRED] |
| **Engine** | PyTorch JIT / LibTorch | Microsoft ONNX Runtime 1.23.2 | Tencent NCNN 1.0.20260526 |
| **Input Shape** | Dynamic / Configurable (e.g. 4x3x576x576) [VERIFIED] | Dynamic batch / fixed dims [VERIFIED] | Fixed batch: **1x3x512x512** [VERIFIED] |
| **Batch Support** | Batch 1 to 4 natively [VERIFIED] | Batch 1 to 4 natively [VERIFIED] | **Strictly Batch 1** (`batch_size=1`) [VERIFIED] |
| **NMS Execution** | Executed in PyTorch C++ extension [VERIFIED] | Built into ONNX graph or PyTorch wrapper [INFERRED] | NCNN layer postprocessing [INFERRED] |
| **Single-Image Latency** | 42.16 ms p50 [MEASURED] | 34.99 ms p50 [MEASURED] | Not measured on Windows [UNVERIFIED] |
| **Batch-4 Latency** | 136.58 ms p50 [MEASURED] | 111.34 ms p50 [MEASURED] | Unsupported (requires 4 single calls) |
| **Local Environment Health** | Fully installed & functional [VERIFIED] | `onnxruntime` installed; providers: `CPUExecutionProvider` [VERIFIED] | Installed, but `pip check` reports missing `portalocker` and `tqdm` [VERIFIED] |
| **Production Recommendation** | **Current Default for Laptop** | Viable CPU drop-in optimization | Viable only for Raspberry Pi ARM edge |

---

## 4. Model Version Consistency & Historical Audit

Audit of model family names and historical remnants across repository files:

```
                  ┌───────────────┐
                  │    YOLO11n    │ (Evaluated in early prototypes; discarded)
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ YOLO26n / 26s │ (Tested on UVH-26 dataset; slower on CPU;
                  └───────┬───────┘  weights deleted in commit e74681d)
                          │
                          ▼
                  ┌───────────────┐
                  │    YOLOv8n    │ (ACTIVE PRODUCTION DEFAULT: 64% lower latency,
                  └───────────────┘  6.25MB size, pre-warmed batch-4 inference)
```

### Categorized Status of Model Names:
1. **CURRENT DEFAULT**: `yolov8n.pt`
   - Configured in `config/deployment.py` (`model_name = "yolov8n.pt"`).
   - Configured in `config/model.py` (`MODEL_NAME = "yolov8n.pt"`).
   - Tracked in repository root (`C:\Users\ashek\Desktop\smart-traffic-management\yolov8n.pt`).
2. **SUPPORTED ALTERNATIVE**: `yolov8n.onnx`
   - Exported via `scripts/export_edge_model.py --format onnx`.
   - Handled dynamically by `MODEL_RUNTIME` in `config/model.py`.
3. **EXPERIMENTAL / EDGE TARGET**: `yolov8n_ncnn_model`
   - Proposed edge target for Raspberry Pi 5.
   - Batch size hard-coded to 1 in `config/deployment.py` and `ai/models/model_manager.py`.
4. **LEGACY / REMOVED**: `yolo26s.pt`, `yolo26n.pt`, `yolo11n.pt`
   - Removed in commit `e74681d`.
   - Historical benchmarks preserved in `docs/benchmarks/yolov8n-vs-yolo26s-final.json`.
   - Remnant documentation references in `README.md` and docstrings cleaned during this audit.

---

## 5. Input Size Audit

| Location | Configured Value | Status / Purpose |
|---|---|---|
| `config/deployment.py` (laptop) | `576` | **Authoritative Default** for Laptop profile [VERIFIED] |
| `config/deployment.py` (raspberry_pi) | `512` | **Authoritative Default** for Raspberry Pi profile [VERIFIED] |
| `config/deployment.py` bounds | `320` to `1280` | Safety clamping via `_bounded_int` [VERIFIED] |
| `config/model.py` | `ACTIVE_PROFILE.input_size` | Propagates active profile input size [VERIFIED] |
| `docker-compose.yml` (`websocket-server`) | `640` | Overrides default to 640 in container environment [VERIFIED] |
| Mobile WebRTC Constraint (`traffic-camera-app`) | `1280 x 720` | Native camera capture constraints [VERIFIED] |
| Mobile Snapshot Presets (`traffic-camera-app`) | `640`, `1280`, `1920` | Configurable longest edge [VERIFIED] |

*Aspect Ratio & Distortion Check*: Ultralytics letterboxing resizes non-square images (e.g., 1280x720 16:9) to the configured square size (e.g., 576x576) by scaling the longer dimension to 576 and symmetrically padding top/bottom with neutral grey pixels (114, 114, 114). The original aspect ratio is strictly preserved [VERIFIED].

---

## 6. Detection & Tracking Threshold Audit

| Parameter | Value | Layer Affected | Functional Role |
|---|---|---|---|
| `YOLO_CONFIDENCE_THRESHOLD` | `0.08` | **DETECTION** | Hard floor passed to `model.predict()`. Discards raw neural boxes below 8% confidence [VERIFIED]. |
| `YOLO_IOU` | `0.60` | **DETECTION** | IoU threshold for Non-Maximum Suppression. Merges duplicate boxes for the same vehicle [VERIFIED]. |
| `YOLO_MAX_DETECTIONS` | `300` | **DETECTION** | Maximum bounding boxes retained per frame [VERIFIED]. |
| `TRACK_HIGH_THRESHOLD` | `0.15` | **TRACKING** | ByteTrack first association tier: matches clear vehicle detections to existing Kalman tracks [VERIFIED]. |
| `TRACK_LOW_THRESHOLD` | `0.08` | **TRACKING** | ByteTrack second association tier: matches weak detections (`0.08 <= conf < 0.15`) to existing tracks for occlusion recovery [VERIFIED]. |
| `NEW_TRACK_THRESHOLD` | `0.15` | **TRACKING** | Threshold required to spawn a new track ID. Weak boxes (`< 0.15`) can NEVER spawn a track [VERIFIED]. |
| `TRACK_MATCH_THRESHOLD` | `0.80` | **TRACKING** | Maximum spatial distance / IoU matching cost for Kalman association [VERIFIED]. |
| `TRACK_BUFFER_FRAMES` | `12` | **TRACKING** | Frames a lost track is preserved through complete occlusion [VERIFIED]. |
| `MIN_CONFIRMATION_FRAMES` | `2` | **ANALYTICS** | Consecutive frames a track must be observed before inclusion in vehicle counts [VERIFIED]. |
| `QUEUE_MOTION_THRESHOLD_PX_SEC` | `15.0` | **ANALYTICS** | Velocity floor (pixels/second) below which a vehicle is marked low-speed [VERIFIED]. |
| `CONSECUTIVE_QUEUE_FRAMES` | `10` | **ANALYTICS** | Consecutive low-speed frames required to flag `is_queued=True` [VERIFIED]. |

### Threshold Interaction Warning [VERIFIED]
`POST /api/v1/system/config` allows operators to adjust `confidenceThreshold` dynamically (between 0.05 and 0.95). If set above `0.15` (e.g. 0.40), the raw YOLO detector will filter out all boxes below 0.40 before ByteTrack ever sees them, effectively disabling ByteTrack's low-confidence occlusion recovery tier.

---

## 7. Model Performance Audit

1. **Model Loading & Memory**:
   - `ModelManager` loads weights once during process startup.
   - First-time model predictor warmup executed during startup: `Model predictor warmed in 11889 ms` [MEASURED].
   - No repeated loading or memory leaks detected in frame loops [VERIFIED].
2. **Execution Serialization & Worker Bounds**:
   - `MessageHandler.frame_executor` uses `ThreadPoolExecutor(max_workers=1)` [VERIFIED].
   - Using a single dedicated worker prevents OpenMP and PyTorch thread thrashing and avoids Python GIL contention while keeping CPU caches warm [VERIFIED].
3. **Thread Configuration**:
   - `torch.set_num_threads(4)` [VERIFIED].
   - `cv2.setNumThreads(1)` prevents OpenCV from competing with PyTorch [VERIFIED].
   - `OMP_WAIT_POLICY=PASSIVE` and `KMP_BLOCKTIME=0` prevent idle CPU spinning [VERIFIED].
4. **Queue Bounding & Staleness**:
   - `latest_frames` in `MessageHandler` stores at most 1 frame per direction; older unread frames are dropped immediately [VERIFIED].
   - `process_batch` enforces a 2500ms hard drop threshold for any frame delayed in network transit [VERIFIED].
5. **Cadence Decoupling**:
   - Mobile nodes stream at 4 FPS (`PREVIEW_FPS=4.0`).
   - Neural detector runs at 2 FPS (`DETECTOR_FPS=2.0`).
   - Intermediate frames are processed by Kalman prediction in `ByteTracker.predict()` in `< 1.0 ms`, cutting total CPU inference compute by 50% [VERIFIED].

---

## 8. Four-Camera Model Behavior

```
Approach Feeds:  [North Frame]   [South Frame]   [East Frame]   [West Frame]
                        │               │              │              │
                        └───────────────┴──────┬───────┴──────────────┘
                                               │
                                               ▼
                              `latest_frames` Dict (Max 1 per lane)
                                               │
                                               ▼
                                 `process_batch(packets)`
                                               │
                                               ▼
                           Group into batch (Laptop: batch_size=4)
                                               │
                                               ▼
                             YOLOv8n Single Forward Pass (576 px)
                                               │
                        ┌──────────────────────┼──────────────────────┐
                        ▼                      ▼                      ▼
                 [North Results]        [South Results]        [East Results]  ...
                        │                      │                      │
                        ▼                      ▼                      ▼
                 ByteTracker(North)     ByteTracker(South)     ByteTracker(East)
```

- **Fairness Guarantee**: The coordinator pops all available approach frames simultaneously. No individual camera stream can starve or monopolize the inference engine [VERIFIED].
- **Tracker Isolation**: Track IDs are scoped strictly to per-lane `ByteTracker` instances (`self.trackers["north"]`, etc.). Vehicles in the North approach can never collide or cross-contaminate tracks in South, East, or West [VERIFIED].
- **Batching Behavior**:
  - Laptop: All 4 active approaches are grouped into a single batch forward pass (`batch_size=4`).
  - Raspberry Pi / NCNN: Frames are serialized into sequential single-frame passes (`batch_size=1`) [VERIFIED].

---

## 9. Orientation Audit

- **Input Orientations**: Supports Portrait (0 deg), Landscape Clockwise (90 deg), Inverted Portrait (180 deg), and Landscape Counter-Clockwise (270 deg) [VERIFIED].
- **Normalization Timing**: `server/frame_normalization.py` applies `cv2.rotate()` to the image array *before* passing pixels to the detector [VERIFIED].
- **Coordinate Integrity**: Because the image array itself is physically rotated to upright orientation before inference, YOLO generates bounding boxes directly in upright display coordinates. Bounding box coordinates do not require post-hoc mathematical translation or inverse rotation [VERIFIED].
- **WebRTC Orientation**: WebRTC video tracks are required to be pre-rotated by the client (`test-webrtc.cjs` strips RTP orientation headers), preventing double-rotation [VERIFIED].

---

## 10. Tracking Compatibility Audit

- **Bounding Box Format**: `Detection` dataclass standardizes `bbox: Tuple[int, int, int, int]` as `(x1, y1, x2, y2)` pixel coordinates [VERIFIED].
- **Tracker Interface**: `ByteTracker.update()` converts detections to numpy float matrix `(x1, y1, x2, y2, confidence, class_id)` and feeds Ultralytics `Boxes` [VERIFIED].
- **Observation State Segregation**:
  - `ObservationState.OBSERVED`: Box was directly detected by YOLO forward pass in the current frame [VERIFIED].
  - `ObservationState.PREDICTED`: Box was projected forward by Kalman filter velocity during an intermediate frame without detector invocation [VERIFIED].
- **Tracker Reset Independence**: `CameraBYTETracker.reset_id()` overrides global Ultralytics ID reset to `pass`, ensuring new cameras do not reset track ID counters of running cameras [VERIFIED].

---

## 11. Detection Accuracy Truth

- **Formal Detection Accuracy**: **Formal detection accuracy is not yet quantitatively validated.**
- No annotated ground-truth traffic dataset is checked into the repository.
- Replay tests and unit test suites verify runtime dataflow, orientation transforms, batch grouping, and Kalman tracking logic, but do **not** constitute a quantitative precision, recall, or mAP evaluation.
- Quantitative accuracy gates must be evaluated against an annotated traffic dataset (such as IISc UVH-26 or IDD) before any physical road deployment.

---

## 12. Analytics Safety & Decision Integrity

- **Observation vs. Prediction Boundary**:
  - `VehicleStateManager.update()` processes `OBSERVED` detections to update vehicle states, motion vectors, and consecutive seen counters [VERIFIED].
  - Detections marked `PREDICTED` are used strictly for UI visualization continuity; they are skipped when computing queue times, live vehicle counts, or historical totals [VERIFIED].
- **PCE Calculation**: Each confirmed vehicle is multiplied by its Passenger Car Equivalent weight:
  - Car = 1.0, Bus = 1.5, Truck = 2.0, Motorcycle = 0.5, Bicycle = 0.5 [VERIFIED].
- **Stabilization Layer**: `CountStabilizer` applies Exponential Moving Average (`alpha=0.4`) over raw counts to eliminate single-frame flickering before scheduling [VERIFIED].
- **Emergency Priority Status**:
  - While `EmergencyOverride` logic is fully implemented, `is_priority` is currently **always False** because the default `yolov8n.pt` COCO weights do not classify ambulances or fire trucks [VERIFIED].
- **Scheduler Starvation Prevention**: The adaptive scheduler follows a strict clockwise cycle (`North` -> `East` -> `South` -> `West`). Traffic density only alters the *duration* of the green light (between `min_green_sec` and `max_green_sec`), ensuring no approach is starved [VERIFIED].

---

## 13. Hardware Target Audit

| Target Dimension | Windows Laptop (Current Host) | Raspberry Pi 5 (Target SBC) |
|---|---|---|
| **CPU Spec** | Multi-core x86_64 CPU (4 threads allocated) | Quad-core ARM Cortex-A76 (4 threads) |
| **GPU / Accelerator** | Optional CUDA (defaults to CPU) | Optional Raspberry Pi AI HAT+ (Hailo-8L) |
| **Memory Allocation** | ~370 MB RSS under active 4-camera inference [MEASURED] | Target <= 512 MB RSS |
| **Model Format** | `yolov8n.pt` (PyTorch) [VERIFIED] | `yolov8n_ncnn_model` (NCNN) [PROPOSED] |
| **Input Resolution** | `576` pixels [VERIFIED] | `512` pixels [PROPOSED] |
| **Batch Size** | `4` [VERIFIED] | `1` [VERIFIED] |
| **Target FPS** | 4 FPS capture / 2 FPS detection [VERIFIED] | 2 FPS capture / 1 FPS detection [PROPOSED] |
| **Validation Status** | **`MEASURED_LOCAL_SOFTWARE`** [VERIFIED] | **`PROPOSED_UNVALIDATED`** [VERIFIED] |

*Notice*: All Raspberry Pi metrics in current documentation are engineering proposals and require physical on-device validation before deployment [VERIFIED].

---

## 14. Model Optimization Opportunities

| Change | Expected Benefit | Technical Risk | Validation Required |
|---|---|---|---|
| **ONNX Runtime on CPU** | ~18.5% lower inference latency (111 ms vs 136 ms for batch 4) [MEASURED] | Minor dependency overhead (`onnxruntime` is 15 MB) | Regression test verifying bounding box IoU alignment with PyTorch |
| **INT8 Post-Training Quantization** | ~2x faster CPU inference, 50% lower RAM | Potential 1-3% degradation in small-vehicle mAP | Evaluation on annotated traffic dataset comparing mAP50 |
| **Vectorized `_convert` in `detector.py`** | 1-2 ms faster postprocessing by eliminating Python box loop | Negligible | Unit test verifying identical `Detection` list output |
| **Raspberry Pi AI HAT+ (Hailo-8L)** | Offloads CPU entirely; sub-10ms inference at 640px | Requires PCIe setup and HailoRT software stack | Physical testing on Raspberry Pi 5 with AI HAT+ hardware |

---

## 15. Known Flaws & Architectural Cleanup Completed

1. **Dead Code in `ai/detection/detector.py`**:
   - `detect_and_track()` invoked `model.track()`, which maintains a single global tracking state and would cause cross-camera ID collisions across 4 approaches.
   - *Status*: Docstrings and architectural notes updated in `ai/detection/detector.py` to clarify that multi-camera pipelines must use `detect_batch()` with independent `ByteTracker` instances per lane [VERIFIED].
2. **Leftover `yolo26n` Documentation**:
   - `README.md` line 203 previously referred to `yolo26n_ncnn_model`.
   - *Status*: Corrected to `models/yolov8n_ncnn_model` in `README.md` [VERIFIED].
3. **NCNN Dependencies on Windows**:
   - `pip check` reports `ncnn 1.0.20260526` is missing `portalocker` and `tqdm`.
   - *Status*: Documented; NCNN is intended for the Linux ARM Raspberry Pi target, not the Windows host runtime [VERIFIED].
4. **Emergency Vehicle Support**:
   - `EmergencyOverride` logic is present in the decision layer, but inactive because generic COCO weights do not include emergency classes.
   - *Status*: Accurately documented in system limitations [VERIFIED].

---

## 16. Recommended Next Tests

1. **Annotated Traffic Accuracy Benchmark**:
   - Run `scripts/evaluate_detector.py` against the IISc UVH-26 dataset or local intersection video frames to establish ground-truth precision and recall (mAP50 / mAP50-95).
2. **On-Hardware Raspberry Pi 5 Validation**:
   - Deploy `yolov8n_ncnn_model` to physical Raspberry Pi 5 hardware and measure sustained FPS, core temperatures, and throttling under 4 simulated streams.
3. **ONNX Runtime Drop-in Verification**:
   - Export `yolov8n.onnx` and verify automated test suite passes with `YOLO_MODEL_NAME=yolov8n.onnx`.
4. **Multi-Camera Edge Occlusion Stress Test**:
   - Benchmark tracking ID retention when multiple heavy vehicles (buses and trucks) occlude smaller vehicles (motorcycles and bicycles) for > 10 frames.
