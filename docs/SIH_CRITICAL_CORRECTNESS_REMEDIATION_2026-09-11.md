# SIH Critical Correctness Remediation

Date: 2026-09-11  
Branch: `codex/four-lane-video`  
Scope baseline: commit `c664ff7` (`docs: add SIH technical audit`)

## Outcome

The source-level P0 and P1 correctness findings in the supplied remediation task are
implemented and covered by regression tests. The runtime now fails closed when an
explicitly requested ESP32 is unavailable, separates detector observations from
tracker predictions, applies one authoritative batch/profile configuration, keeps
bounded latest-frame handoffs, bounds file logs, exposes ticker failures, and avoids
fabricated operational telemetry.

This is software verification only. It does not prove physical ESP32 operation,
Raspberry Pi performance, detector accuracy, emergency detection, or public-road
readiness.

## P0 remediation matrix

| Finding | Remediation | Evidence | Status |
|---|---|---|---|
| P0-1 ESP32 mode was forced to simulation | Added explicit `HARDWARE=simulation\|esp32`, required configurable `ESP32_PORT` for hardware, configurable baud, lifecycle states, reconnect/ACK reporting, fail-closed startup, all-red behavior, and actual dashboard state. Removed forced runtime and lazy-path simulation. | Hardware and runtime regression tests cover simulation, configured hardware double, unavailable port, reconnect, ACK, command rejection, and all-red status. | Software-complete; physical device unvalidated |
| P0-2 predictions treated as observations | Added `OBSERVED`/`PREDICTED` semantics. Predictions preserve ID/bbox for display but do not confirm tracks, refresh observation time, advance queue evidence, or enter authoritative analytics. Added last observation/prediction metadata. | Observation regression tests inspect state counters/timestamps and confirmed analytics. | Complete |
| P0-3 NCNN batch mismatch | Added one validated `batch_size`; NCNN forces one. Model warm-up, inference validation, coordinator grouping, and per-frame batch telemetry use the same effective value. | Regression test verifies NCNN warm-up uses one and rejects oversized inference input. | Complete |
| P0-4 temporal architecture | Retained one latest slot per direction and one bounded inference worker. Detector cadence consumes a fresh latest frame and uses trusted server-monotonic receipt time; prediction bridges detector gaps. Trackers remain independent per camera. | Latest-frame replacement, trusted clock, staleness, and tracker isolation tests pass. | Complete |

## P1 remediation matrix

| Finding | Remediation | Evidence | Status |
|---|---|---|---|
| Deployment profiles | Added immutable LAPTOP and RASPBERRY_PI profiles covering capture, WebRTC sample, detector, input, batch, CPU threads, and preview cadence. Effective values are published in runtime telemetry. | Profile validation and cross-component cadence tests pass. Pi is labeled `PROPOSED_UNVALIDATED`. | Complete; Pi unvalidated |
| Hot-path logging | Frame receipt/orientation/normalization/inference and per-lane ranking traces moved to DEBUG. Application and error logs use bounded rotating handlers with bounded environment overrides. | Logging-level and rotating-handler tests pass. | Complete |
| Runtime error visibility | Extracted a testable ticker iteration. Unexpected failures increment the error counter, log exception type/message at ERROR, retain traceback at DEBUG, and continue the ticker; unsafe hardware forces pause. | Failure-injection regression test passes. | Complete |
| Truthful telemetry | Hardware, ACK, resource, inference, frame, and camera metadata now report actual values or `None`/`UNAVAILABLE`/`NOT_CONNECTED`. Removed hard-coded simulation, COM port, baud, 30 FPS, and 8 GB diagnostic fallbacks. | Runtime/API tests and frontend production build pass. | Complete within current sensors |

## File/change/reason/test traceability

| Files | Change | Reason | Test/evidence |
|---|---|---|---|
| `config/deployment.py`, `config/model.py` | Added validated effective profiles and shared model values. | Eliminate conflicting runtime configuration. | `tests/test_deployment_profile.py` |
| `ai/models/model_manager.py`, `server/frame_coordinator.py` | Unified warm-up/inference/coordinator batching and truthful actual batch telemetry. | Prevent NCNN batch-one mismatch. | Deployment profile and coordinator tests |
| `ai/hardware/esp32_interface.py`, `ai/hardware/__init__.py`, `ai/controller/control_manager.py` | Added explicit hardware lifecycle, port/baud, reconnect, ACK, and fail-closed command behavior. | Prevent silent hardware-to-simulation fallback. | `tests/test_control_logging_hardware.py` |
| `server/runtime.py`, `server/message_handler.py`, `core/application_context.py`, `web/services/system_service.py` | Wired effective hardware into both startup paths, safe all-red, health/status, and visible runtime failures. | Make runtime behavior and status agree. | Runtime, web, hardware, and operational tests |
| `ai/detection/detection_types.py`, `ai/tracking/byte_tracker.py`, `ai/state/vehicle_state_manager.py`, `ai/analytics/analytics_exporter.py`, `ai/pipeline/traffic_pipeline.py` | Separated observed evidence from predicted display tracks and restricted analytics to confirmed observations. | Stop predictions from creating demand or queue evidence. | `tests/test_observation_semantics.py`, pipeline tests |
| `server/local_sources.py`, `server/webrtc_ingest.py`, `web/services/camera_service.py`, `server/protocol.py` | Applied profile cadences and removed unknown-source FPS fabrication. | Keep temporal behavior bounded and configurable. | Profile, local source, coordinator, and runtime tests |
| `ai/utils/logger.py`, `ai/signal/priority_calculator.py` | Added bounded rotation and reduced hot-path INFO logs. | Prevent noisy/unbounded operational logs. | `tests/test_operational_logging.py` |
| `ai/camera/camera_stream.py`, `ai/camera/camera_manager.py`, `ai/pipeline/intersection_state.py`, `ai/visualization/visualizer.py`, `web/schemas.py` | Propagated unavailable camera/resource values without fake measurements. | Make telemetry honest. | Camera, web, operational, and pipeline tests |
| `web-ui/src/**`, `web-ui/dist/**` | Display actual ESP32 state/port/baud/error/ACK and unknown values; rebuilt production assets. | Remove misleading dashboard claims without redesigning UI. | `npm run lint`, `npm run build` |
| `tests/test_pipeline_multi_camera.py`, `tests/test_runtime_regressions.py` | Updated integration setup for confirmation and expanded runtime regressions. | Verify corrected two-observation and safe runtime behavior. | Full suite |

## Tests added

Twenty-three regression tests were added across:

- `tests/test_deployment_profile.py`
- `tests/test_observation_semantics.py`
- `tests/test_operational_logging.py`
- `tests/test_control_logging_hardware.py`
- `tests/test_runtime_regressions.py`

They cover the requested categories: simulation, hardware startup, unavailable serial,
ACK, reconnect, safe fallback, observed/predicted updates, confirmation, observation
timestamp, queue evidence, NCNN batch-one warm-up, latest-frame replacement,
per-camera isolation, staleness, logging level, and exception visibility.

## Verification results

Baseline before remediation:

- Python suite: `78 passed, 1 warning`.

Final combined verification:

- `python -m pytest -q --timeout=60`: `101 passed, 1 warning in 31.27s`.
- `python -m compileall -q ai config core server web run.py`: passed (exit 0, no output).
- `npm run lint`: passed (`tsc --noEmit`, exit 0).
- `npm run build`: passed; Vite transformed 1502 modules and emitted production assets.
- `git diff --check`: passed before the implementation commits; only Git's Windows LF/CRLF notices were printed.

The remaining warning is the existing Starlette/httpx `TestClient` deprecation warning.
It is unrelated to these correctness changes.

## Hardware mode verification

| Mode | Verified behavior |
|---|---|
| Explicit simulation | State is `SIMULATION`; no physical ACK is fabricated. |
| ESP32 with serial double | Configured port/baud are used; state becomes `CONNECTED`; ACK content/time are retained. |
| ESP32 unavailable | State remains `ERROR`, not simulation; commands are rejected, startup is paused, and signal telemetry is `ALL_RED`. |
| Reconnect | A failed initial connection can retry and transition to `CONNECTED`. |

No physical ESP32 was connected during verification, so electrical signaling, firmware
compatibility, USB stability, and real ACK timing remain unverified.

## Observation versus prediction verification

An observed box may update confirmation, last observation frame/time, motion, and queue
evidence. A predicted box may update its last prediction frame and projected display
bbox, but cannot refresh the observation timestamp, increment confirmation, keep a
vehicle analytically alive, or create queue/PCE/priority input. Confirmed observations
alone feed the analytics exporter; intermediate preview frames reuse the last
authoritative detector statistics rather than recomputing demand from predictions.

## NCNN batch verification

When the configured model name identifies an NCNN export, the effective profile forces
`batch_size=1`. Warm-up uses a one-image list, coordinator groups contain at most one,
inference rejects larger input, and telemetry records the actual group size (zero on a
prediction-only frame). No NCNN throughput claim is made.

## Remaining limitations

- Raspberry Pi values are proposed and unvalidated; benchmark them on the target Pi.
- Physical ESP32 and firmware integration require bench testing with the real device.
- Detector accuracy requires a held-out, labelled traffic dataset; no accuracy claim is made.
- Emergency-vehicle recognition and reinforcement learning are not implemented.
- REST operator controls are unauthenticated and local camera/WebSocket traffic is cleartext by default; use only on a trusted LAN.
- The Starlette/httpx test-client deprecation should be handled in a dependency-maintenance change.
- This prototype is not certified or validated for public-road signal control.
