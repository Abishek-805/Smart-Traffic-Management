# Multi-Repository Test Strategy & Quality Verification

## 1. Quality Architecture Overview

The Smart Traffic Management System enforces a multi-tier testing hierarchy across both independent repositories:
1. **Backend & Control Center (`smart-traffic-management`)**: Python 3.12 / pytest / FastAPI TestClient.
2. **Mobile Node (`traffic-camera-app`)**: TypeScript / Node test runners / Expo React Native.
3. **Frontend Dashboard (`web-ui`)**: TypeScript / Vite / React.

Every software change must pass automated gates before merge.

---

## 2. Test Hierarchy

```
                               ┌─────────────────────────────┐
                               │       E2E Replay Lab        │  Tier 5: 6 Scenarios
                               │   (ai/pipeline/replay_lab)  │
                               └──────────────┬──────────────┘
                                              │
                               ┌──────────────┴──────────────┐
                               │  Property & Invariants      │  Tier 4: Safety & Fairness
                               │(tests/test_safety_invariants│
                               └──────────────┬──────────────┘
                                              │
                               ┌──────────────┴──────────────┐
                               │  API Negative & Boundaries  │  Tier 3: 14 HTTP/WS Tests
                               │ (tests/test_api_negative.py)│
                               └──────────────┬──────────────┘
                                              │
                               ┌──────────────┴──────────────┐
                               │  Subsystem & Integration    │  Tier 2: Tracking, Calibration
                               │ (Evaluation, Schedulers)    │
                               └──────────────┬──────────────┘
                                              │
                               ┌──────────────┴──────────────┐
                               │  Core Unit & Regression     │  Tier 1: 101 Base Tests
                               │ (tests/test_runtime_regress)│
                               └─────────────────────────────┘
```

---

## 3. Test Suites & Descriptions

### Tier 1: Core Subsystems & Regressions (101 tests)
- **Startup & Configuration** (`test_startup.py`, `test_deployment_profile.py`): Profile boundary validation, environment variable overrides, thread bounds.
- **Perception & Tracking** (`test_batch_detection.py`, `test_observation_semantics.py`, `test_pipeline_multi_camera.py`): Independent ByteTrackers, observation vs. prediction separation.
- **Traffic Analytics & Scheduling** (`test_priority_calculator.py`, `test_signal_controller.py`, `test_signal_scheduler.py`, `test_fairness_manager.py`, `test_emergency_override.py`): PCE scoring, queue motion thresholds, adaptive ratio green calculation, emergency boost.
- **Hardware & Logging** (`test_control_logging_hardware.py`, `test_operational_logging.py`, `test_local_sources.py`): Mock ESP32 serial interface, CSV/JSON log persistence, local video feeds.
- **Communications** (`test_communication_server.py`, `test_frame_coordinator.py`, `test_webrtc_ingest.py`, `test_e2e_pipeline_websocket.py`): WebSocket session management, frame decoding, WebRTC handshakes.

### Tier 2: Model Evaluation & Metric Calibration (9 tests)
- **Model Evaluation Lab** (`test_model_evaluation.py`): IoU computations, precision/recall envelopes, mAP@50 and mAP@50:95, count MAE/RMSE, COCO JSON and YOLO txt annotation parsing.
- **Queue Calibration** (`test_queue_calibration.py`): Perspective homography transform ($[u, v] \to [X, Y]$ in meters), metric queue calculation, uncalibrated scale fallback.

### Tier 3: Negative Boundary & Security Tests (14 tests)
- **REST Negative Boundaries** (`test_api_negative.py`): Rejection of invalid directions (HTTP 422), non-configurable cameras (HTTP 422), confidence limits ($< 0.05$ or $> 0.95$), green duration limits ($5 \le t_{min} \le t_{max} \le 120$), pagination bounds (`limit=0`, `limit=2000`).
- **WebSocket Protocol Rejections**: Malformed packets, missing message type, version mismatch, invalid pairing token, unauthorized session frame injection.
- **Operator Authentication Enforcement**: HTTP 401 Unauthorized verification when `OPERATOR_API_KEY` is configured and header is missing or incorrect.

### Tier 4: Property & Safety Invariants (6 tests)
- **Mutual Exclusion**: Never allows $> 1$ green phase active simultaneously; non-green directions must be red.
- **Clearance Enforcement**: Yellow ($\ge 3\text{s}$) and clearance intervals are mandatory before phase switches.
- **Strict Clamping**: Green durations strictly clamped within $[MIN\_GREEN\_SEC, MAX\_GREEN\_SEC]$ under zero or infinite demand.
- **Anti-Starvation**: Clockwise round-robin guarantees every demand lane is served within 4 cycles regardless of opposing congestion.
- **Prediction Immunity**: Kalman predicted tracks never increment confirmed vehicle counts.
- **Stale Frame Drop**: Frames older than $2500\text{ ms}$ are dropped immediately.

### Tier 5: Traffic Replay Lab & Scenario Simulation (4 tests)
- Executes multi-step intersection simulations under `BALANCED_NORMAL`, `HEAVY_NORTH`, `ALL_BUSY_GRIDLOCK`, `CAMERA_DISCONNECT`, and `EMERGENCY_PREEMPTION`.
- Validates telemetry collection, dynamic green adjustments, and dropout tolerance.

### Tier 6: Mobile Node Verification (Traffic Camera App)
- `scripts/test-regressions.cjs`: Token issuance, server backpressure, RTT measurement, node identity, QR orientation, TLS URL parsing.
- `scripts/test-webrtc.cjs`: WebRTC timing, frame pacing, connection retries, cleanup.
- TypeScript compilation: `npm run type-check` (`tsc --noEmit`) ensures zero type errors.

### Tier 7: Frontend Web UI Verification
- Production build: `npm run build` (`tsc && vite build`) compiles static bundle in $< 1\text{s}$ with zero warnings.

---

## 4. Execution Commands

```powershell
# 1. Full Backend Test Suite (134 tests)
cd C:\Users\ashek\Desktop\smart-traffic-management
.\.venv\Scripts\python.exe -m pytest -v

# 2. Mobile Node Tests & Type Check
cd C:\Users\ashek\Desktop\traffic-camera-app
npm test
npm run type-check

# 3. Frontend Web UI Build
cd C:\Users\ashek\Desktop\smart-traffic-management\web-ui
npm run build

# 4. Multi-Camera Benchmark
cd C:\Users\ashek\Desktop\smart-traffic-management
.\.venv\Scripts\python.exe scripts\benchmark_inference.py
```
