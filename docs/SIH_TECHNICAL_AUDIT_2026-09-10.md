# SIH Technical, Model, and Performance Audit

**Project:** Smart Traffic Management System

**Audit date:** 10 September 2026

**Audited branch:** `codex/four-lane-video`

**Companion application:** `Traffic_Camera_App`, mobile release 1.0.7

## 1. Executive verdict

The project is a functioning four-approach traffic-management prototype with a
sound high-level pipeline:

```text
Four Android cameras
  -> authenticated WebSocket/WebRTC ingestion
  -> bounded latest-frame coordinator
  -> YOLOv8n vehicle detection
  -> independent ByteTrack state per approach
  -> vehicle, queue, and PCE analytics
  -> fairness-aware signal scheduling
  -> hardware command generation
  -> React operations dashboard
```

The current implementation has credible software evidence for local four-camera
operation. It is not yet ready to claim Raspberry Pi readiness, measured traffic
accuracy, physical ESP32 control from the primary web runtime, or public-road
deployment. The main blockers are summarized below.

1. The combined web runtime forces ESP32 simulation mode.
2. The active detector has not passed a representative labelled accuracy gate.
3. Projected tracker states are treated as observations in vehicle confirmation
   and queue analytics.
4. The NCNN edge startup path warms the model with a four-image batch even though
   the runtime treats NCNN as batch-one.
5. Operator APIs and QR generation have no authentication, and the default LAN
   transport is unencrypted.

These findings do not invalidate the prototype. They define the work required to
turn a successful demonstration into a defensible engineering system.

## 2. Audit scope and method

The audit covered:

- detector loading, warm-up, inference, batching, thresholds, and runtime profiles;
- ByteTrack integration, observation cadence, track confirmation, and queue state;
- four-camera coordination, backpressure, staleness, and WebRTC sampling;
- signal safety behavior and ESP32 integration paths;
- REST, WebSocket, pairing, and operator-control security;
- Python and web dependency health;
- React dashboard type-checking and production build;
- the companion Android camera application's capture and connection paths;
- existing validation reports, benchmark records, and documentation consistency;
- likely SIH jury questions and the evidence available to answer them.

This was a software-only audit. No Raspberry Pi, ESP32, physical phones, or
representative labelled traffic dataset was available. Hardware behavior, Wi-Fi
endurance, electrical timing, and real traffic accuracy therefore remain open
validation items.

## 3. Verification evidence

### 3.1 Checks completed successfully

| Check | Result |
|---|---|
| Python test suite | 78 passed in 21.79 seconds |
| Python bytecode compilation | Passed |
| React/TypeScript type-check | Passed |
| React production build | Passed; 315.13 kB JavaScript, 93.65 kB gzip |
| Dashboard dependency audit | Zero reported vulnerabilities |
| Four-camera integrated smoke test | Passed registration, processing, independent staleness, Stop, and Start |
| Mobile TypeScript type-check | Passed |
| Mobile connection regression script | Passed when invoked directly |
| Mobile WebRTC regression script | Passed when invoked directly |
| Expo dependency compatibility | Dependencies match the installed Expo SDK |

The integrated smoke test used four authenticated local clients and the real
YOLOv8n model. It verifies software integration, not physical phones, Wi-Fi, or
detector accuracy.

### 3.2 Warnings and failed health checks

- `pip check` reported that the installed `ncnn` package is missing
  `portalocker` and `tqdm`.
- The Python suite emitted a Starlette/httpx deprecation warning.
- The mobile project does not expose its existing regression scripts through
  `package.json`; `npm run test:regressions` and `npm run test:webrtc` fail with
  missing-script errors.
- The mobile production dependency audit reported 15 advisories: 9 high and
  6 moderate. The affected dependency chains include XML parsing, React
  Navigation, and Metro tooling. Exploitability must be assessed rather than
  applying breaking `--force` upgrades blindly.
- Expo Doctor passed 16 of 17 checks and reported that `react-native-webrtc`
  is not recorded as tested on React Native's New Architecture.
- No Python linter, formatter gate, static type gate, coverage threshold, or CI
  workflow is configured.

## 4. Prioritized findings

### P0-1: Primary web runtime cannot select physical ESP32 control

`server/runtime.py` constructs `ControlManager(simulation_mode=True,
headless=True)` unconditionally. The fallback construction in
`server/message_handler.py` does the same. The dashboard capability snapshot is
also hard-coded to report `hardware: "SIMULATION"`.

**Impact:** The normal `start.ps1` -> `run.py` web workflow cannot control a real
ESP32 even though `ESP32Interface` and the separate startup wizard contain serial
support. A jury demonstration through the React dashboard will always be a
simulation.

**Required correction:** Load an explicit hardware profile at startup, discover
or accept the selected serial port, construct one authoritative `ControlManager`,
and publish its measured connection/ACK state. Retain simulation as a safe,
visible fallback.

### P0-2: Detector accuracy is not established

The active model is generic `yolov8n.pt` at 576 pixels with a confidence floor of
0.08. Existing calibration evidence is based on a very small sample and earlier
model candidates. There is no representative labelled result for the current
weights, resolution, camera height, lighting, occlusion, or Indian vehicle mix.

**Impact:** Counts, PCE, queue estimates, and signal decisions inherit unknown
false-positive and false-negative rates. More detections do not prove better
accuracy.

**Required evidence:** Report precision, recall, mAP50, mAP50-95, per-class
recall, count MAE, queue-count error, and tracking ID switches on held-out traffic
video. Include motorcycles, bicycles, buses, trucks, three-wheelers, rain, night,
occlusion, and distant vehicles.

### P0-3: Tracker projections can become analytical observations

The detector runs at a lower cadence than incoming frames. On intermediate
frames, `ByteTracker.predict()` returns projected tracks. The pipeline then sends
those projections through `VehicleStateManager.update()` exactly like detector
observations. This increments `consecutive_seen_frames`, refreshes
`last_seen_timestamp`, and can contribute to stopped/queue state.

**Impact:** A vehicle may become confirmed after only one actual detector
observation. Projected tracks can influence live counts and queue timing without
new visual evidence.

**Required correction:** Distinguish observed from predicted track updates.
Predictions may support display continuity, but only real detector observations
should confirm tracks, refresh observation timestamps, or update queue evidence.

### P0-4: NCNN startup batch conflicts with the edge runtime policy

`ModelManager._load_model()` always warms the predictor with four images.
`server/frame_coordinator.py` separately defaults NCNN inference to batch size
one because exported runtimes may only support batch-one.

**Impact:** An NCNN model can fail during startup before the batch-one runtime
policy takes effect. This blocks or weakens the Raspberry Pi path.

**Required correction:** Define a single validated batch-size setting and use it
for warm-up and inference. The Raspberry Pi/NCNN profile should default to one.

### P1-1: Operator controls and QR generation are unauthenticated

The API exposes QR generation, Start, Stop, Restart, configuration, camera feed,
logs, and camera disconnection without operator authentication.

**Impact:** Any device with trusted-LAN access can create pairing credentials,
change timing/confidence settings, stop the system, view feeds, or disconnect a
camera.

**Required correction:** Add authenticated operator sessions and authorization
for control routes. Pairing QR generation must require operator authorization.
Use TLS/WSS outside an isolated demonstration LAN.

### P1-2: Per-frame INFO logging adds avoidable hot-path overhead

The server logs orientation, normalization, YOLO start, YOLO completion, priority
ranking, and other events for individual frames. Four active cameras can create
many log entries per second.

**Impact:** Avoidable formatting, terminal output, file I/O, disk growth, and
benchmark noise.

**Required correction:** Move frame-level traces to DEBUG, sample periodic
operational metrics, rotate files, and keep warnings and state changes at INFO.

### P1-3: Camera and detector cadence are not unified by deployment profile

The mobile WebRTC source requests 1280x720 at 5 FPS. The server samples WebRTC at
a fixed four FPS, while detector cadence is separately configured at two FPS on
the laptop and one FPS in the proposed Pi profile.

**Impact:** The Pi may still decode and track more frames than required even when
detector FPS is reduced. Configuration intent is spread across mobile and server
constants.

**Required correction:** Define explicit laptop and Pi profiles covering capture
FPS, WebRTC sample FPS, detector FPS, input size, batch size, thread count, and
preview rate. Publish the effective profile in health telemetry.

### P1-4: Dependency installation is not reproducible

Most Python dependencies use broad lower bounds. The audited environment contains
much newer packages than the minimums, has an incomplete NCNN installation, and
emits a framework deprecation warning.

**Impact:** A clean laptop or Pi installation may behave differently from the
audited machine.

**Required correction:** Maintain tested lock/constraint files per platform,
verify them in CI, and include an explicit edge runtime dependency set.

### P1-5: Documentation identifies multiple active models

`docs/PROJECT_CONTEXT.md` describes YOLO11, the beginning of
`docs/OPTIMIZATION_REPORT.md` declares YOLO26s/YOLO26n defaults, and current
configuration/status documentation declares YOLOv8n.

**Impact:** A jury cannot determine which model produced which metric, and stale
claims undermine otherwise valid benchmark evidence.

**Required correction:** Make YOLOv8n the single documented active baseline,
mark previous comparisons as historical, and attach every measurement to the
exact weights, runtime, resolution, confidence, device, and commit.

### P1-6: Mobile dependency advisories require controlled remediation

The companion application's production audit reports 15 advisories. Some simple
updates are available, while other automated recommendations propose breaking
Expo or navigation changes.

**Impact:** Known vulnerable transitive dependencies remain in the build tool and
application dependency tree.

**Required correction:** Apply non-breaking lockfile updates first, determine
whether vulnerable parsers are reachable in the packaged application, and plan
SDK/navigation upgrades with a native Android regression build. Do not use
`npm audit fix --force` without reviewing the resulting major-version changes.

### P2-1: Mobile WebRTC ignores the selected camera facing

`WebRTCPreview` always calls `session.start('back', ...)`, so the Settings screen's
front/rear selection does not affect the preferred WebRTC path.

### P2-2: Existing mobile tests are not part of the package workflow

The regression files exist and pass when run directly, but `package.json` contains
no corresponding scripts. They are therefore easy to omit from local and CI
verification.

### P2-3: Queue motion is expressed as fixed pixels per second

A fixed 15 px/s threshold changes physical meaning with resolution, perspective,
mounting height, crop, and distance from the camera.

**Required correction:** Calibrate per-camera road-plane/ROI behavior or normalize
motion by object scale and image geometry. Validate stopped-vehicle classification
against annotated video.

### P2-4: Exception visibility is incomplete

The runtime ticker catches broad exceptions and increments a counter without
logging the traceback. This preserves availability but makes intermittent
scheduler/hardware failures difficult to diagnose.

## 5. Performance analysis and optimization headroom

### 5.1 Existing measured baseline

The current project records the following local four-WebRTC-peer result at the
576-pixel laptop profile:

- approximately 2.95-3.0 processed updates per lane per second;
- direction p95 server latency of approximately 633-679 ms;
- p95 batched inference of approximately 472-509 ms;
- p95 queue wait of approximately 217-226 ms.

This is valid evidence for local replay through desktop WebRTC peers. It is not a
physical Wi-Fi, Android thermal, or Raspberry Pi measurement.

### 5.2 Fresh isolated CPU comparison

The audit repeated one supplied real-image fixture with YOLOv8n, four CPU threads,
confidence 0.08, IoU 0.60, and four-image batches. This is a runtime comparison,
not an accuracy result.

| Model input | Batch-four p50 | Batch-four p95 | Approx. batch throughput | Speed-up over four sequential calls |
|---:|---:|---:|---:|---:|
| 448 | 79.36 ms | 88.73 ms | 50.43 FPS | 1.36x |
| 512 | 106.29 ms | 120.08 ms | 38.29 FPS | 1.23x |
| 576, current | 134.36 ms | 146.60 ms | 30.05 FPS | 1.16x |
| 640 | 146.96 ms | 165.60 ms | 26.92 FPS | 1.12x |

On this isolated fixture, 448 pixels reduced batch p50 by about 41% relative to
576. This does **not** justify changing the default. Small and distant vehicle
recall must be compared on labelled data first. The same fixture also produced a
different low-confidence detection count at 640 pixels, demonstrating why a
single-image count cannot serve as an accuracy gate.

### 5.3 Safe optimizations that do not require changing model accuracy

1. Use profile-aware warm-up and inference batch sizes.
2. Remove per-frame INFO logging from the hot path.
3. Separate tracker predictions from observation-backed analytics.
4. Use a server monotonic clock for cadence and freshness decisions while keeping
   client timestamps for transport-latency telemetry.
5. Make WebRTC decode/sample rate configurable per deployment profile.
6. Cache or reuse immutable conversion metadata where profiling proves benefit.
7. Benchmark preview JPEG work separately from detector latency.
8. Add p50, p95, p99, drop-rate, stale-frame rate, decode time, tracking time,
   CPU, RSS, temperature, and hardware ACK metrics to one repeatable report.

### 5.4 Optimizations that require accuracy or hardware evidence

- reducing input from 576 to 512, 448, or 416 pixels;
- changing confidence, IoU, ByteTrack, or queue thresholds;
- quantization to FP16 or INT8;
- selecting PyTorch, ONNX Runtime, NCNN, or Hailo compiled inference;
- changing the detector family or model scale;
- lowering detector FPS;
- fine-tuning on UVH-26 or locally collected intersection data.

Each candidate must be compared on the same labelled validation set and target
hardware. Latency alone is not sufficient.

## 6. Laptop and Raspberry Pi profiles

### 6.1 Laptop profile

The current laptop is an Intel Core i5-13450HX with 10 physical cores, 16 logical
processors, and approximately 16 GB RAM. Four PyTorch CPU threads, one persistent
pipeline executor, latest-frame replacement, and four-image batching are reasonable
measured defaults.

The laptop acceptance gate should include:

- all four physical phones connected for at least 60 minutes;
- no unbounded RSS or thread growth;
- at least 99% session availability under normal Wi-Fi;
- explicitly chosen p95 freshness and server-latency limits;
- labelled count and queue accuracy;
- recovery from phone backgrounding, Wi-Fi loss, and server restart;
- verified ESP32 ACKs and safe all-red failover.

### 6.2 Raspberry Pi profile

The documented Pi profile is a proposal, not a measured deployment. Begin with a
Pi 5, 64-bit OS, active cooling, batch-one NCNN, 512 pixels, and one detector update
per lane per second. The actual choice must follow a benchmark on the intended Pi.

Measure:

- inference and end-to-end p50/p95/p99 latency;
- sustained CPU utilization, throttling, temperature, and RSS;
- camera frame freshness and drop rate;
- detector and tracking accuracy using identical labelled inputs;
- serial command/ACK latency and behavior during brownout or reconnect;
- performance with four simultaneous physical phones.

If CPU-only Pi performance cannot meet the freshness requirement, use a Pi AI
HAT+/Hailo path or retain the laptop as the inference controller. Do not claim
performance based on TOPS marketing figures; show an end-to-end measured result.

## 7. SIH jury cross-question sheet

### What part of the project uses AI?

YOLOv8n performs vehicle detection. ByteTrack provides temporal association. The
signal scheduler is an explainable deterministic controller using PCE, queue,
congestion, fairness, and safety timing. It is not reinforcement learning.

### Why was YOLOv8n selected?

On the audited laptop it is substantially faster and smaller than previously
tested larger candidates. It provides the best current throughput baseline, but
final selection still depends on labelled local-traffic accuracy.

### What does real-time mean in this system?

The system intentionally processes sampled fresh frames rather than 30 FPS video.
The current local four-peer evidence shows about three processed updates per lane
per second. Freshness and bounded latency matter more than retaining every frame.

### How is overload controlled?

There is one latest-frame slot per direction. A newer frame replaces a pending
older frame, so backlog cannot grow indefinitely. The mobile client also checks
socket backpressure, and the WebRTC receiver keeps only its latest decoded frame.

### How is starvation prevented?

The scheduler uses fairness-aware clockwise service and bounded green durations.
Occupied low-demand approaches must still receive service instead of being
permanently dominated by a high-demand approach.

### What happens when a camera fails?

Each direction becomes stale independently. Unavailable approaches are excluded
from fresh traffic input. If no usable input remains, the displayed/controller
state falls back to all-red. Physical relay and ESP32 fail-safe behavior still
requires hardware validation.

### Does emergency vehicle priority work?

The override rule exists and is tested as control logic, but the active COCO
detector does not recognize emergency vehicles. Live emergency recognition must
not be claimed.

### What accuracy has been achieved?

No representative accuracy figure is currently defensible for the active model.
The project has runtime measurements and a small exploratory calibration sample,
not a complete held-out accuracy evaluation.

### Why use four phones?

Each phone observes one approach, avoiding the occlusion and perspective limitations
of assigning four road approaches from a single arbitrary image. Phones make the
prototype accessible, but permanent deployment would use fixed, weather-rated,
calibrated cameras.

### Can this run on a Raspberry Pi?

The code has an NCNN export path and a conservative proposed Pi profile. It has not
been benchmarked on a physical Pi, so readiness cannot yet be claimed.

### Is the ESP32 physically controlled?

The serial interface and command encoder exist. The primary combined web runtime
currently forces simulation, so physical dashboard-to-ESP32 control is an open P0
integration task.

### Is it safe for a public junction?

No. The current system is a trusted-LAN prototype. Public deployment requires
authentication, TLS, calibrated accuracy, redundant fail-safe hardware, regulatory
review, physical endurance testing, audit logging, and a documented manual override.

### How is this better than fixed-time signaling?

It can allocate bounded green duration using observed per-approach demand while
preserving fairness. The actual reduction in average delay or queue length must be
demonstrated in a controlled baseline experiment; it should not be claimed without
before/after data.

### Why not use reinforcement learning?

A deterministic scheduler is easier to explain, test, constrain, and fail safely
for a prototype. Reinforcement learning would require a validated simulator,
reward design, transfer testing, and safety constraints. It is not necessary to
demonstrate adaptive demand-based control.

### What are the privacy implications?

The system processes traffic video and exposes live previews. A deployment needs
data-minimization rules, retention limits, access control, encryption, signage or
legal review as applicable, and confirmation that number plates/faces are not
retained without authority.

## 8. Recommended remediation plan

### Phase 1: Correctness and honest hardware status

1. Separate observed and predicted track updates with regression tests.
2. Make warm-up respect the configured runtime batch size.
3. Wire an explicit ESP32/simulation profile into the combined runtime.
4. Replace hard-coded hardware capability text with measured interface state.
5. Log runtime ticker failures with bounded, actionable diagnostics.

### Phase 2: Performance and deployment profiles

1. Add laptop and Pi profile files with validated bounds.
2. Configure WebRTC sample rate rather than fixing it at four FPS.
3. Reduce hot-path logging and enable log rotation.
4. Extend benchmarks to report decode, inference, tracking, preview encode, queue,
   CPU, RSS, temperature, and dropped/stale frames separately.
5. Fix and verify the batch-one NCNN installation path.

### Phase 3: Engineering quality and security

1. Add operator authentication and authorization to mutating routes and QR creation.
2. Document or configure TLS/WSS for non-isolated networks.
3. Add Python constraints/lock files for laptop and Pi.
4. Register mobile regression scripts in `package.json`.
5. Add CI for backend tests, Python static checks, frontend/mobile type-checks,
   builds, regression scripts, and dependency audits.
6. Remediate mobile dependency advisories through reviewed, compatible upgrades.

### Phase 4: Accuracy and physical validation

1. Prepare a representative labelled dataset and a held-out test split.
2. Evaluate the current YOLOv8n baseline at candidate input sizes.
3. Fine-tune the nano model for the local vehicle taxonomy.
4. Measure detection, count, queue, and tracking metrics.
5. Benchmark the accepted model on the actual Pi and laptop.
6. Run four-phone endurance, orientation, lighting, congestion, and Wi-Fi recovery
   tests.
7. Validate ESP32 timing, ACKs, watchdog behavior, all-red failover, and manual
   override on physical hardware.

## 9. Acceptance gates before stronger claims

The project should not claim the following until the matching evidence exists:

| Claim | Minimum evidence |
|---|---|
| Accurate vehicle detection | Held-out precision, recall, mAP, and per-class results |
| Accurate traffic counts | Count MAE/MAPE on labelled video |
| Accurate queue detection | Stopped/queued precision and recall with calibrated geometry |
| Raspberry Pi ready | Sustained four-source benchmark on the actual target Pi |
| ESP32 integrated | Dashboard-to-device command and ACK tests on real hardware |
| Real-time | Defined freshness/latency SLO and sustained p95/p99 result |
| Emergency priority | Validated emergency detector plus safe override test |
| Production/public-road ready | Security, fail-safe, regulatory, privacy, and field validation |
| Improves traffic flow | Controlled comparison against a fixed-time baseline |

## 10. Final assessment

The project already demonstrates several good engineering choices: bounded
latest-frame processing, authenticated camera sessions, independent approach
tracking, explicit stale-camera behavior, explainable scheduling, startup model
warm-up, repeatable benchmarks, and honest documentation of several limitations.

The next step should not be an unmeasured model replacement. The strongest path is
to correct observation semantics and edge startup, connect truthful ESP32 status,
reduce avoidable runtime overhead, and then select model/resolution/runtime using
labelled accuracy and real target-hardware evidence. That sequence gives the team
defensible answers to SIH jury questions without overstating prototype results.
