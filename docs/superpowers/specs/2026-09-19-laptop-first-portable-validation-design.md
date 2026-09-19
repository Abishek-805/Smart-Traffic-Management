# Laptop-First Portable Validation Design

**Date:** 2026-09-19  
**Status:** Approved design direction  
**Target branch:** `codex/four-lane-video`

## 1. Objective

Finish and validate the complete software stack on a development laptop while keeping Raspberry Pi 5 deployment concerns isolated behind configuration and adapters. The project must improve incrementally; it must not replace the working Mobile Camera -> Backend -> YOLOv8n -> ByteTrack -> Traffic Analytics -> Signal Scheduler -> Dashboard architecture.

The completed software may claim laptop validation for multi-camera reliability, latency, recovery, model evaluation, scheduler behavior, security, replay, and long-duration operation. It may claim only that a Raspberry Pi deployment profile is prepared and resource-aware until the application is benchmarked on physical Raspberry Pi hardware.

## 2. Constraints and principles

- No Raspberry Pi, AI accelerator, ESP32, or physical signal hardware is currently available.
- Laptop tests are the authoritative software acceptance environment.
- Hardware and thermal behavior are represented through interfaces, simulated inputs, and resource-constrained tests, not presented as physical validation.
- Existing APIs and working behavior remain compatible unless a documented correctness or security requirement requires a versioned change.
- Each phase is a bounded increment and must keep the existing regression suite green.
- Latency and accuracy changes require measured evidence. A faster runtime or smaller input is not accepted if it causes an unapproved accuracy regression.
- Experimental perception features remain disabled by default behind explicit feature flags.
- Queues remain bounded and overload favors current information over processing stale frames.

## 3. Existing capabilities to preserve and extend

The repository already contains important foundations:

- QR-authenticated camera registration and direction ownership.
- WebRTC ingest plus JPEG compatibility paths.
- A latest-frame coordinator with per-direction slots and stale-frame handling.
- YOLOv8n detection, independent ByteTrack state, traffic analytics, and scheduling.
- Laptop and Raspberry Pi deployment profiles.
- Model warm-up and runtime benchmarks.
- Homography-based calibration support.
- Model evaluation and recorded replay utilities.
- Operator authentication, safety invariants, digital-intersection tests, and audit documents.

Implementation must strengthen these components rather than create parallel replacements.

## 4. Selected architecture

### 4.1 Portable runtime boundary

Platform-dependent behavior is exposed through narrow adapters:

- `FrameSource`: WebRTC, JPEG, recorded file, future Picamera2/USB/RTSP.
- `InferenceRuntime`: current PyTorch/Ultralytics baseline, optional future ONNX, NCNN, or accelerator runtime.
- `SystemMetricsProvider`: Windows/Linux laptop metrics and a future Raspberry Pi provider.
- `SignalOutput`: simulation/digital intersection now and a future ESP32 adapter.

Core detection, tracking, analytics, scheduling, telemetry contracts, and safety rules do not import platform-specific camera, GPIO, or Raspberry Pi libraries.

Runtime capability detection selects only supported adapters. Unsupported hardware features report `unavailable`; they do not silently simulate successful hardware operation.

### 4.2 Multi-camera data flow and backpressure

Each camera direction owns one replaceable pending frame slot. Receipt of a newer frame replaces an older unprocessed frame for that direction. There is no unbounded per-camera work queue.

The coordinator chooses due directions fairly, rejects frames beyond the configured age limit, and submits work according to the measured runtime. On the laptop CPU baseline, latency-sensitive single-frame or micro-batch execution is preferred when local benchmarks show that a four-frame batch increases service time and frame age. Batch size is a profiled deployment setting, not a fixed architectural assumption.

Only confirmed, sufficiently fresh observations may update scheduling demand. Dropped or stale frames do not become zero traffic. The last confirmed state remains visible with an explicit stale status.

### 4.3 Camera lifecycle and ownership

A camera progresses through explicit states:

```text
OFFLINE -> PAIRING -> CONNECTING -> LIVE
                         |           |
                         v           v
                       ERROR <-> DEGRADED
                         |
                         v
                    RECONNECTING
```

The backend distinguishes signalling, media transport, frame receipt, inference freshness, and application heartbeat. A registered socket without usable media is not reported as `LIVE`.

Direction ownership has a documented takeover rule:

1. A healthy authenticated owner cannot be displaced by a different node.
2. A reconnect carrying the same valid session identity may replace its dead transport immediately.
3. An abandoned or transport-dead owner becomes reclaimable after a short, explicit grace period instead of requiring a server restart.
4. A conflicting active node receives a structured `DIRECTION_OCCUPIED` response containing retry guidance.
5. Cleanup is idempotent, so simultaneous disconnect and timeout handling cannot remove a newly established owner.

### 4.4 Latency and transport observability

Every processed frame carries monotonic timestamps for capture when available, server receive, decode completion, coordinator selection, inference start/end, analytics completion, and response/publication. Telemetry reports at least:

- source FPS and dimensions;
- decoded and accepted FPS;
- detector FPS;
- network/arrival age where clocks permit;
- decode time;
- coordinator wait;
- inference time;
- analytics and rendering time;
- total server time;
- end-to-end frame age;
- replacement, stale-drop, decode-failure, and inference-failure counts.

WebRTC clients use the standardized statistics surface for packet loss, jitter, frame dimensions, decoded/sent FPS, encode/decode time where exposed, and jitter-buffer delay. The dashboard identifies the actual transport instead of a hard-coded JPEG label.

### 4.5 Fairness and adaptive cadence

The coordinator uses round-robin eligibility among due, fresh directions. One high-rate phone cannot permanently consume the inference runtime. Per-direction counters demonstrate offered, selected, processed, replaced, and stale-dropped frames.

An optional adaptive controller changes detector cadence within configured bounds using recent inference service time, active camera count, frame age, and overload state. It does not alter model confidence thresholds or input resolution automatically. Cadence changes are observable and reversible.

## 5. Model-quality architecture

### 5.1 Repository-controlled evaluation manifest

The repository defines a versioned manifest and annotation schema without committing restricted or large external datasets. A manifest records dataset identity, split, source/license, image or video reference, dimensions, scene tags, annotation revision, and checksum.

Supported annotations cover bounding boxes, class labels, optional track IDs, optional queue-region membership, and ignore regions. Scene tags include day/night, rain, glare, occlusion, portrait/landscape, small-object density, and India-specific vehicle/road conditions.

External datasets such as BDD100K remain separate from project-owned validation footage. Public-dataset results and local-domain results are never blended into one unexplained score.

### 5.2 Evaluation outputs and gates

Reports include:

- per-class precision, recall, AP, and aggregate mAP;
- false-positive and false-negative examples;
- metrics split by scene tag and object size;
- count mean absolute error per frame or interval;
- tracking ID switches and track continuity where track annotations exist;
- latency, throughput, memory, model/runtime identity, input size, and hardware description.

The current YOLOv8n configuration remains the baseline. A candidate model, export, quantization mode, input size, or tracking change must pass declared accuracy and performance thresholds against the same immutable evaluation split. An optimization that improves speed but violates the accuracy allowance is rejected.

### 5.3 Additional perception

Tracking changes first target stable counts and identity continuity. Calibrated queue estimation uses configured queue polygons and optional homography/world coordinates; it must fall back to labelled image-space estimates when calibration is absent.

Additional features such as lane segmentation, stopped-vehicle detection, speed estimation, or new vehicle subclasses are experiments behind flags. They are promoted only after dataset coverage, accuracy evidence, and resource impact are documented.

The existing COCO-based weights must not be described as validated ambulance or fire-engine detectors. Emergency perception requires dedicated labels and a separately evaluated method.

## 6. Scheduler and explainability

The scheduler consumes a versioned demand snapshot containing observation age and health. A decision record is emitted for every selection, extension, release, fallback, or preemption. It contains:

```text
Selected: SOUTH
Demand: HIGH
Vehicles: 11
Queue: 6
PCE: 11.0
Observation age: 0.3 s
Current phase: SOUTH GREEN
Decision reason: HIGHEST_DEMAND_SCORE
```

Reason codes are stable machine-readable values with human-readable explanations. Records also include alternatives considered, constraints that affected the decision, minimum/maximum green bounds, fairness/max-wait state, emergency state, configuration revision, and timestamp.

Emergency scheduling is validated with simulated, authenticated emergency events. Tests cover preemption entry, conflicting events, minimum safe transitions, event expiry, return to normal operation, and audit history. The UI and documentation clearly label simulated emergency input.

## 7. Testing laboratory

### 7.1 Deterministic replay

Recorded inputs run through the production normalization, inference, tracking, analytics, and scheduler path with a controllable clock. A replay seed and configuration snapshot make results reproducible.

Golden scenarios cover congestion changes, empty lanes, stale lanes, clockwise fairness, maximum wait, emergency events, reconnects, malformed frames, and source orientation. Replay output can be compared structurally rather than relying only on screenshots.

### 7.2 Multi-camera and network simulation

Laptop tests create one to four independent camera producers with configurable resolution, orientation, source FPS, burstiness, disconnects, delay, jitter, loss, reordering where relevant, and corrupted payloads. Tests assert bounded memory, direction isolation, fair progress, stale-frame rejection, and recovery without restarting the server.

WebRTC network impairment may be applied through a supported development proxy or browser/network test mechanism. Where the test harness cannot alter real RTP conditions reliably, the limitation is reported and equivalent ingest timing behavior is tested at the application boundary.

### 7.3 Resource-limit and soak testing

Selected laptop tests run with constrained CPU availability and memory budgets to expose overload behavior. These tests approximate resource pressure but are not labelled as Raspberry Pi performance predictions because they do not reproduce ARM instruction performance, Pi camera drivers, thermals, or an accelerator.

Soak tests monitor throughput, frame age, process RSS, threads/tasks, connection count, exception count, queue/slot occupancy, reconnect success, and scheduler progress. Short CI soaks catch regressions; a documented local long soak provides stronger release evidence.

## 8. Security design

- Pairing credentials are cryptographically random, scoped to a node/direction, short-lived, and single-use or explicitly rotated.
- Authentication is checked at connection establishment and authorization is rechecked for sensitive messages.
- Reconnect tokens and session identifiers cannot be reused by another node or direction.
- A replay cache rejects previously consumed registration nonces/tokens until expiry.
- Message type, size, schema, frame dimensions, encoded size, and rate are bounded before expensive decoding or inference.
- Per-IP, per-node, and global rate limits protect registration, signalling, frame submission, and operator APIs.
- Logs capture connection, authentication, authorization, validation, rate-limit, takeover, abnormal disconnect, and administrative events without recording secrets or raw credentials.
- Origin and transport-security policy are configurable for production while local development remains usable.

Security tests cover expired/replayed tokens, oversized and malformed messages, direction spoofing, unauthorized takeover, flood limits, and operator authorization.

## 9. Deployment profiles

Three explicit profiles are maintained:

```text
laptop
raspberry-pi-5
accelerated
```

Profiles specify source adapters, runtime, model artifact, input size, batch policy, inference cadence, thread settings, memory limits, preview settings, and metrics provider. Environment variables may override documented values, and the effective configuration is exposed with secrets redacted.

The Raspberry Pi metrics adapter will expose CPU temperature, clock, undervoltage, frequency-capped, soft-temperature-limit, and current/historical throttling flags when `vcgencmd` is available. On a laptop these fields report `unsupported`; tests use a fake provider to verify warning and degradation policy.

ONNX, NCNN, or accelerator exports are later candidates, not assumed improvements. Each is accepted only after the same accuracy corpus, cold/warm startup, single-camera, multi-camera, and soak benchmarks pass.

## 10. Phased delivery and acceptance gates

### Phase 1: correctness and reliability

- First connection succeeds without a server restart in repeated clean trials.
- Same-session reconnect and eligible stale-owner takeover behave deterministically.
- Camera states reflect signalling, media, frames, and inference truthfully.
- Pending frame work is bounded to one replaceable slot per direction.
- A failing camera does not block or corrupt another direction.

### Phase 2: performance and telemetry

- Benchmarks compare current batching with latency-oriented execution using identical videos and settings.
- Two and four active sources make fair progress without unbounded frame age or memory growth.
- Telemetry separates transport/frame age, decode, coordinator, inference, and post-processing time.
- Model warm-up occurs before readiness is advertised.
- Adaptive cadence, if enabled, stays within bounds and records every change.
- Numeric release thresholds are established from the corrected baseline rather than invented before measurement.

### Phase 3: model quality

- Versioned manifest/schema, evaluator, and immutable baseline report exist.
- Reports include per-class and difficult-scene breakdowns.
- CI has a small deterministic regression corpus; full local evaluation is documented separately.
- Runtime/model changes cannot merge when defined accuracy or latency allowances fail.

### Phase 4: traffic perception

- Count stability and tracking metrics improve or remain within the approved regression allowance.
- Queue calibration has validation examples and an explicit uncalibrated fallback.
- Experimental features are disabled by default and separately measured.

### Phase 5: emergency handling

- Simulated emergency lifecycle and scheduler safety tests pass.
- UI and audit history identify simulation versus detected/physical input.
- No unvalidated emergency-vehicle detection claim is made.

### Phase 6: explainability

- Every scheduler decision has a stable reason code and input snapshot.
- Dashboard and exported history show freshness, health, constraints, and alternatives.
- Replay can reproduce a decision from the recorded configuration and observations.

### Phase 7: testing lab

- Replay, multi-camera load, impairment, recovery, scheduler failure, and soak workflows are repeatable from documented commands.
- Failures produce machine-readable artifacts suitable for comparison.

### Phase 8: security

- Pairing, replay protection, validation, rate limiting, and audit tests pass.
- Development allowances are explicit and cannot silently become production defaults.

### Phase 9: deployment abstraction

- Laptop remains the fully validated environment.
- Pi and accelerated profiles load without importing unavailable platform packages.
- Fake platform metrics verify resource-warning behavior.
- Documentation labels all Pi throughput, thermal, camera, GPIO, and power results as `not hardware validated` until measured on a physical device.

## 11. Verification strategy

Every implementation phase runs the narrow tests for changed behavior followed by the complete repository regression suite. Performance phases also save machine-readable benchmark artifacts containing commit, configuration, model hash, source details, warm-up policy, trial counts, and environment.

A release evidence summary distinguishes:

- automated laptop tests;
- manual laptop/mobile-device tests;
- simulated resource/hardware behavior;
- future physical Raspberry Pi/ESP32 tests.

Claims are derived from those categories and never generalized across them without measurements.

## 12. External engineering basis

- W3C WebRTC statistics define standardized packet, jitter, FPS, frame-dimension, decode-time, and jitter-buffer measurements suitable for transport diagnosis: <https://www.w3.org/TR/webrtc-stats/>.
- Raspberry Pi documents `vcgencmd measure_temp`, clocks, and `get_throttled` bit flags; these inform the future metrics adapter but do not substitute for a physical benchmark: <https://www.raspberrypi.com/documentation/computers/os.html>.
- Raspberry Pi documents thermal throttling beginning around 80 degrees Celsius and recommends active cooling for sustained performance: <https://www.raspberrypi.com/documentation/computers/raspberry-pi.html>.
- Raspberry Pi AI HAT+ provides an official future vision-acceleration route, but its benefit must be measured on the final workload: <https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html>.
- Ultralytics documents NCNN as an ARM-oriented deployment option; it remains a benchmark candidate subject to project-specific accuracy parity: <https://docs.ultralytics.com/guides/raspberry-pi/>.
- BDD100K provides diverse road-scene detection and tracking tasks, useful as an external benchmark alongside separate India-specific data: <https://github.com/bdd100k/bdd100k>.
- OWASP's WebSocket Security guidance supports authentication, authorization, validation, size/rate limits, and security-event logging: <https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html>.

## 13. Explicit non-goals

- A wholesale rewrite of the backend or mobile protocol.
- Training a new production model before a labelled evaluation baseline exists.
- Claiming detection of emergency subclasses from generic COCO vehicle classes.
- Claiming Raspberry Pi FPS, thermals, stability, power use, Picamera2 behavior, accelerator behavior, or ESP32 electrical safety from laptop simulation.
- Automatically lowering resolution, confidence, or model size merely to improve an FPS number.
- Adding cloud infrastructure or internet-facing operation to this iteration.

## 14. Final defensible project statement

> The complete software stack is validated on the laptop, including multi-camera reliability, latency, recovery, model evaluation, scheduler behavior, security, and long-duration operation. A Raspberry Pi 5 deployment profile is prepared and resource-aware, but physical Pi performance and hardware integration are reported separately until measured on the actual hardware.
