# Multidisciplinary Engineering Improvement Backlog

This backlog records prioritized engineering improvements, technical debt remediation, and future production readiness tasks across the Smart Traffic Management System.

---

## Priority Classification

- **P0 — Correctness & Safety**: Must be implemented to prevent unsafe operations, crashes, or security breaches.
- **P1 — Performance & Core Functionality**: High-impact improvements to latency, throughput, and cross-subsystem reliability.
- **P2 — Accuracy & Quality**: Enhancements to visual detection, calibration, tracking precision, and dataset evaluation.
- **P3 — Usability & Maintainability**: Developer experience, observability, UI responsiveness, and code ergonomics.
- **P4 — Experimental & Future**: Edge optimizations (NCNN/TensorRT), physical relay hardware, and municipal network infrastructure.

---

## Item Inventory

### [P0-1] Operator REST Endpoint Authentication
- **Problem**: REST modifying endpoints (`/system/config`, `/system/start`, `/system/stop`, `/system/restart`, `DELETE /cameras/{direction}`) were previously open to any client on the local network.
- **Evidence**: [`web/routes/api_routes.py`](file:///C:/Users/ashek/Desktop/smart-traffic-management/web/routes/api_routes.py#L70-L131) executed commands without verifying bearer or header tokens.
- **Impact**: Rogue LAN devices could disconnect cameras or alter signal green durations maliciously.
- **Proposed Solution**: Introduce optional `OPERATOR_API_KEY` environment configuration with `X-Operator-Token` header verification. Permissive fallback for demo mode with warning log.
- **Implementation**: Created `verify_operator_auth` dependency in [`web/routes/api_routes.py`](file:///C:/Users/ashek/Desktop/smart-traffic-management/web/routes/api_routes.py#L30-L38).
- **Test**: Automated tests in [`tests/test_api_negative.py:test_operator_auth_enforcement`](file:///C:/Users/ashek/Desktop/smart-traffic-management/tests/test_api_negative.py) verifying 401 rejections.
- **Measurement**: 100% rejection of unauthorized requests when key is configured; 0 overhead when unset.
- **Status**: `IMPLEMENTED & VERIFIED`.

---

### [P0-2] Signal Controller Conflicting Green Invariant
- **Problem**: Need mathematical assurance that the signal scheduler and controller never emit commands with multiple simultaneous green lights.
- **Evidence**: Previous tests checked nominal output but did not codify invariant assertions across arbitrary demand distributions.
- **Impact**: Simultaneous conflicting green lights at a physical intersection cause catastrophic vehicle collisions.
- **Proposed Solution**: Add property tests asserting mutual exclusion, yellow clearance $\ge 3\text{s}$, and all-red $\ge 2\text{s}$.
- **Implementation**: Implemented [`tests/test_safety_invariants.py`](file:///C:/Users/ashek/Desktop/smart-traffic-management/tests/test_safety_invariants.py).
- **Test**: `test_invariant_mutual_exclusion_of_greens` and `test_invariant_clearance_intervals_preservation`.
- **Measurement**: 100% pass rate across all simulated phase combinations.
- **Status**: `IMPLEMENTED & VERIFIED`.

---

### [P1-1] Multi-Camera Traffic Replay & Scenario Regression Lab
- **Problem**: Evaluating the multi-camera pipeline previously required manual execution or separate synthetic scripts.
- **Evidence**: Lack of a standardized programmatic regression lab that tests multi-approach dynamics (gridlock, camera dropout, emergency preemption).
- **Impact**: Difficult to verify scheduler fairness and timing regressions under complex traffic scenarios.
- **Proposed Solution**: Build a `TrafficReplayLab` simulating balanced traffic, heavy North, gridlock, dropouts, and emergency preemption.
- **Implementation**: Added [`ai/pipeline/replay_lab.py`](file:///C:/Users/ashek/Desktop/smart-traffic-management/ai/pipeline/replay_lab.py).
- **Test**: [`tests/test_traffic_replay_lab.py`](file:///C:/Users/ashek/Desktop/smart-traffic-management/tests/test_traffic_replay_lab.py) (4 automated scenario tests).
- **Measurement**: Deterministic phase allocations and cycle timings logged for every scenario.
- **Status**: `IMPLEMENTED & VERIFIED`.

---

### [P1-2] Frame Ingestion Stale-Drop Watchdog
- **Problem**: High network jitter or client lag can queue delayed frames, causing stale actuation decisions based on outdated traffic states.
- **Evidence**: Monitored by `time.time() * 1000 - packet['backend_receive_timestamp'] > 2500`.
- **Impact**: Green light granted to vehicles that have already departed, causing intersection inefficiency.
- **Proposed Solution**: Enforce a hard drop policy on frames arriving older than $2500\text{ ms}$.
- **Implementation**: Bounded check in [`server/frame_coordinator.py:process_batch`](file:///C:/Users/ashek/Desktop/smart-traffic-management/server/frame_coordinator.py#L28-L30).
- **Test**: [`tests/test_safety_invariants.py:test_invariant_stale_frame_rejection`](file:///C:/Users/ashek/Desktop/smart-traffic-management/tests/test_safety_invariants.py).
- **Measurement**: Stale frames dropped with `dropped` stage counter incremented; zero latency spillover.
- **Status**: `IMPLEMENTED & VERIFIED`.

---

### [P2-1] Ground-Plane Metric Queue Calibration Architecture
- **Problem**: Queue estimation using raw pixels ($15\text{ px/s}$, pixel distance) does not reflect real-world metric distance (meters) due to camera perspective distortion.
- **Evidence**: Near-field vehicles occupy 4x more pixels than far-field vehicles.
- **Impact**: Falsely overestimates near-field queues while underestimating far-field vehicle queues.
- **Proposed Solution**: Implement 4-point perspective homography ($H$) mapping image coordinates $[u, v]$ to road metric coordinates $[X, Y]$ (meters).
- **Implementation**: Implemented [`ai/analytics/calibration.py`](file:///C:/Users/ashek/Desktop/smart-traffic-management/ai/analytics/calibration.py).
- **Test**: [`tests/test_queue_calibration.py`](file:///C:/Users/ashek/Desktop/smart-traffic-management/tests/test_queue_calibration.py) (4 tests verifying transformation, inverse mapping, and fallback).
- **Measurement**: True distance in meters calculated for calibrated lanes; clean fallback to default scale when uncalibrated.
- **Status**: `IMPLEMENTED & VERIFIED`.

---

### [P2-2] Reusable Model Evaluation Lab & Accuracy Tooling
- **Problem**: Repo contains no ground-truth traffic dataset, leading to unverified accuracy claims in old reports.
- **Evidence**: No evaluation scripts existed for computing mAP, confusion matrices, or vehicle count errors.
- **Impact**: Unable to evaluate fine-tuned or pruned models objectively before deployment.
- **Proposed Solution**: Create a standardized `ModelEvaluator` supporting COCO JSON and YOLO TXT annotations, computing mAP@50, mAP@50:95, per-class F1, confusion matrices, and count MAE/RMSE.
- **Implementation**: Implemented [`ai/evaluation/model_evaluator.py`](file:///C:/Users/ashek/Desktop/smart-traffic-management/ai/evaluation/model_evaluator.py).
- **Test**: [`tests/test_model_evaluation.py`](file:///C:/Users/ashek/Desktop/smart-traffic-management/tests/test_model_evaluation.py) (5 tests passing).
- **Measurement**: Accurate metric calculation across known bounding box geometries.
- **Status**: `IMPLEMENTED & VERIFIED`.

---

### [P3-1] CPU Threading & Contention Optimization
- **Problem**: Running PyTorch YOLOv8n with 8 threads on laptop CPUs caused thread contention, increasing latency.
- **Evidence**: `scripts/benchmark_inference.py` measured 8 threads at p50 = 279.47 ms vs 2 threads at p50 = 84.64 ms!
- **Impact**: 3.3x slower inference when using excessive CPU threads.
- **Proposed Solution**: Bound default inference CPU threads to 2–4 threads in deployment profiles.
- **Implementation**: Bounded in `config/deployment.py` and `scripts/benchmark_inference.py`.
- **Test**: Verified via `benchmark_inference.py`.
- **Measurement**: 84.64 ms p50 achieved at 2 threads vs 279.47 ms at 8 threads.
- **Status**: `MEASURED & VERIFIED`.

---

### [P4-1] Raspberry Pi 5 NCNN Runtime Field Compilation
- **Problem**: NCNN runtime is specified in `RaspberryPiProfile`, but `.param` and `.bin` compiled assets are not pre-bundled.
- **Evidence**: Only PyTorch FP32 weights exist on disk.
- **Impact**: Deploying to Raspberry Pi 5 currently requires manual compilation via `yolo export format=ncnn`.
- **Proposed Solution**: Create automated cross-compilation pipeline or build workflow to package NCNN FP16 weights for ARM64.
- **Test**: Benchmarking on physical Pi 5 board.
- **Status**: `BACKLOG — P4`.

---

### [P4-2] Physical Conflict Monitor Unit (CMU) Hardware Interlock
- **Problem**: Software fail-closed logic is verified, but physical electrical conflict monitoring (preventing dual greens at relay coil level) requires electrical design.
- **Evidence**: Mock ESP32 interface simulates commands; no physical relay interlock circuit exists.
- **Impact**: If microcontroller firmware hangs or hardware short-circuits, software cannot intervene physically.
- **Proposed Solution**: Design relay interlock circuit where Green relays physically cut power to conflicting Green coils.
- **Test**: Physical circuit continuity and fault injection.
- **Status**: `BACKLOG — P4 (HARDWARE DEPENDENCY)`.
