# SIH Critical Correctness Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct hardware-mode truth, observation-versus-prediction semantics, NCNN batch consistency, deployment profiles, hot-path logging, runtime error visibility, and telemetry honesty without replacing YOLOv8n or changing the mobile protocol.

**Architecture:** Add one immutable deployment profile as the source of effective runtime settings, and inject it through model loading, WebRTC sampling, hardware startup, and telemetry. Preserve the latest-frame coordinator and independent trackers, while tagging detections as observed or predicted so only detector-backed evidence changes confirmation and queue analytics.

**Tech Stack:** Python 3.12, FastAPI, Ultralytics YOLOv8n, ByteTrack, PySerial, pytest, React/TypeScript, Vite.

**Spec:** `C:/Users/ashek/.codex/attachments/99c2c5e2-19be-436c-9908-5721c280bcab/pasted-text.txt`

## Global Constraints

- Work only from current source code; do not use historical task logs.
- Keep YOLOv8n and the current mobile WebSocket protocol.
- Preserve existing functionality and the safe all-red behavior.
- Do not redesign unrelated UI.
- Do not make unmeasured performance, accuracy, Pi, public-road, emergency-detection, or physical-ESP32 claims.
- Write each behavior test first, run it to observe the intended failure, implement the minimum correction, and rerun relevant tests.
- Use explicit unavailable/unknown states instead of fabricated operational values.

---

### Task 1: Authoritative deployment profile and batch configuration

**Files:**
- Create: `config/deployment.py`
- Modify: `config/model.py`
- Modify: `ai/models/model_manager.py`
- Modify: `server/frame_coordinator.py`
- Test: `tests/test_deployment_profile.py`
- Test: `tests/test_runtime_regressions.py`

**Interfaces:**
- Produces: `DeploymentProfile`, `load_deployment_profile(environ=None)`, and `ACTIVE_PROFILE`.
- Produces: profile fields `name`, `validation_status`, `hardware_mode`, `serial_port`, `serial_baudrate`, `capture_fps`, `webrtc_sample_fps`, `detector_fps`, `input_size`, `batch_size`, `cpu_threads`, and `preview_fps`.
- Consumes: environment variables `TRAFFIC_PROFILE`, `HARDWARE`, `ESP32_PORT`, `ESP32_BAUDRATE`, and existing `YOLO_*` overrides.
- Test utility: `build_model_manager_with_fake_yolo(monkeypatch, model_name, batch_size)` patches only the external Ultralytics loader and returns the real `ModelManager` with recorded predictor calls.

- [ ] **Step 1: Write failing profile and NCNN warm-up tests**

```python
def test_laptop_profile_has_measured_runtime_defaults():
    profile = load_deployment_profile({"TRAFFIC_PROFILE": "laptop"})
    assert profile.name == "LAPTOP"
    assert profile.validation_status == "MEASURED_LOCAL_SOFTWARE"
    assert profile.batch_size == 4

def test_pi_profile_is_explicitly_unvalidated_and_batch_one():
    profile = load_deployment_profile({"TRAFFIC_PROFILE": "raspberry_pi"})
    assert profile.name == "RASPBERRY_PI"
    assert profile.validation_status == "PROPOSED_UNVALIDATED"
    assert profile.batch_size == 1

def test_ncnn_warmup_uses_configured_batch_one(monkeypatch):
    manager = build_model_manager_with_fake_yolo(monkeypatch, model_name="models/best_ncnn_model", batch_size=1)
    assert len(manager.model.predict_calls[0]["source"]) == 1
```

- [ ] **Step 2: Run the focused tests and confirm they fail because deployment/profile and batch interfaces do not exist**

Run: `python -m pytest tests/test_deployment_profile.py tests/test_runtime_regressions.py -q`

- [ ] **Step 3: Implement immutable profiles and make model settings derive from the active profile**

```python
@dataclass(frozen=True)
class DeploymentProfile:
    name: str
    validation_status: str
    hardware_mode: str
    serial_port: str | None
    serial_baudrate: int
    capture_fps: float
    webrtc_sample_fps: float
    detector_fps: float
    input_size: int
    batch_size: int
    cpu_threads: int
    preview_fps: float
```

Validate profile names, hardware modes, numeric bounds, and the requirement that
`HARDWARE=esp32` supplies `ESP32_PORT`. Keep laptop defaults aligned with current
measured software settings; label Raspberry Pi defaults `PROPOSED_UNVALIDATED`.

- [ ] **Step 4: Use one batch size for warm-up, inference grouping, and telemetry**

Pass `batch_size` into `ModelManager`, warm with exactly that many frames, bound
`predict_batch()` by it, and read the same value in `frame_coordinator.py`. NCNN
must resolve to batch-one even when a conflicting override is supplied.

- [ ] **Step 5: Run focused and full tests**

Run: `python -m pytest tests/test_deployment_profile.py tests/test_runtime_regressions.py tests/test_batch_detection.py tests/test_frame_coordinator.py -q`

- [ ] **Step 6: Commit the profile/batch correction**

```powershell
git add config/deployment.py config/model.py ai/models/model_manager.py server/frame_coordinator.py tests/test_deployment_profile.py tests/test_runtime_regressions.py docs/superpowers/plans/2026-09-10-sih-critical-correctness-remediation.md
git commit -m "fix: unify deployment and model batch profiles"
```

### Task 2: Truthful ESP32 hardware lifecycle

**Files:**
- Modify: `ai/hardware/esp32_interface.py`
- Modify: `ai/controller/control_manager.py`
- Modify: `server/runtime.py`
- Modify: `server/message_handler.py`
- Modify: `core/application_context.py`
- Test: `tests/test_control_logging_hardware.py`
- Test: `tests/test_runtime_regressions.py`

**Interfaces:**
- Produces: `HardwareConnectionState` values `SIMULATION`, `CONNECTING`, `CONNECTED`, `DISCONNECTED`, and `ERROR`.
- Produces: truthful `HardwareStatus.connection_state`, ACK state, and error state.
- Produces: `hardware_is_safe_to_run(status: HardwareStatus) -> bool`, used by startup to pause an unavailable explicitly requested controller.
- Consumes: `ACTIVE_PROFILE.hardware_mode`, `serial_port`, and `serial_baudrate`.
- Test utilities: `fake_serial`, `failing_serial`, and `flaky_serial` replace only the external PySerial boundary and implement open, write, flush, read, and close behavior.

- [ ] **Step 1: Write failing hardware lifecycle tests**

```python
def test_simulation_startup_reports_simulation():
    interface = ESP32Interface(simulation_mode=True)
    assert interface.get_status().connection_state == "SIMULATION"

def test_requested_hardware_connects_to_configured_port(fake_serial):
    interface = ESP32Interface(port="TEST_PORT", simulation_mode=False)
    assert interface.get_status().connection_state == "CONNECTED"

def test_unavailable_requested_hardware_reports_error_without_claiming_simulation(failing_serial):
    interface = ESP32Interface(port="MISSING_PORT", simulation_mode=False)
    status = interface.get_status()
    assert status.connection_state == "ERROR"
    assert status.simulation_mode is False

def test_hardware_reconnect_recovers_from_error(flaky_serial):
    interface = ESP32Interface(port="TEST_PORT", simulation_mode=False)
    assert interface.reconnect() is True
    assert interface.get_status().connection_state == "CONNECTED"

def test_valid_ack_is_recorded(fake_serial):
    assert ESP32Interface(port="TEST_PORT", simulation_mode=False).send_command(command) is True

def test_failed_requested_hardware_is_not_safe_to_run():
    status = HardwareStatus(simulation_mode=False, connection_state="ERROR")
    assert hardware_is_safe_to_run(status) is False
```

- [ ] **Step 2: Run the hardware tests and confirm failures identify forced simulation and missing connection states/reconnect**

Run: `python -m pytest tests/test_control_logging_hardware.py tests/test_runtime_regressions.py -q`

- [ ] **Step 3: Implement explicit ESP32 state transitions**

Simulation reports `SIMULATION`. Requested hardware reports `CONNECTING` during
open, `CONNECTED` after success, `ERROR` after open/write failure, and
`DISCONNECTED` after a clean close. A failed hardware request must not relabel
itself as simulation. `reconnect()` must close stale serial state and retry the
configured port.

- [ ] **Step 4: Construct one profile-driven ControlManager in the combined runtime**

Use `simulation_mode=profile.hardware_mode == "simulation"`, the configured serial
port, and baud rate. Remove both unconditional `simulation_mode=True` constructions.
If explicit ESP32 startup fails, leave `ctx.system_running=False`, preserve
all-red output, expose `ERROR`, and keep the dashboard available for diagnosis.

- [ ] **Step 5: Publish actual hardware state instead of a constant capability**

Build hardware telemetry from `ctx.control_manager.esp32_interface.get_status()`.
Expose connection state, configured mode, port only when meaningful, last ACK,
last error, and command count without inventing values.

- [ ] **Step 6: Run focused and full hardware/runtime tests**

Run: `python -m pytest tests/test_control_logging_hardware.py tests/test_runtime_regressions.py tests/test_web_application.py -q`

- [ ] **Step 7: Commit the hardware correction**

```powershell
git add ai/hardware/esp32_interface.py ai/controller/control_manager.py server/runtime.py server/message_handler.py core/application_context.py tests/test_control_logging_hardware.py tests/test_runtime_regressions.py
git commit -m "fix: report and enforce real ESP32 runtime state"
```

### Task 3: Observation-versus-prediction semantics

**Files:**
- Modify: `ai/detection/detection_types.py`
- Modify: `ai/tracking/byte_tracker.py`
- Modify: `ai/state/vehicle_state_manager.py`
- Modify: `ai/pipeline/traffic_pipeline.py`
- Modify: `ai/visualization/visualizer.py`
- Test: `tests/test_runtime_regressions.py`
- Test: `tests/test_pipeline_multi_camera.py`

**Interfaces:**
- Produces: `ObservationType(str, Enum)` with `OBSERVED` and `PREDICTED`.
- Produces on detections/states: `observation_type`, `last_observation_frame_id`, `last_prediction_frame_id`, and `last_observation_timestamp`.
- Preserves: predicted boxes and track IDs for display continuity.

- [ ] **Step 1: Write failing observed-state tests**

```python
def test_observed_track_refreshes_observation_metadata():
    state = manager.update([observed_detection], frame_number=10, timestamp=5.0)[0]
    assert state.observation_type == ObservationType.OBSERVED
    assert manager.active_states[7].last_observation_frame_id == 10
    assert manager.active_states[7].last_observation_timestamp == 5.0

def test_second_observation_can_confirm_vehicle():
    manager.update([observed_detection], frame_number=10, timestamp=5.0)
    manager.update([observed_detection], frame_number=12, timestamp=6.0)
    assert manager.active_states[7].is_confirmed is True
```

- [ ] **Step 2: Write failing prediction-safety tests**

```python
def test_prediction_cannot_confirm_vehicle():
    manager.update([observed_detection], frame_number=10, timestamp=5.0)
    manager.update([predicted_detection], frame_number=11, timestamp=5.5)
    assert manager.active_states[7].is_confirmed is False

def test_prediction_cannot_refresh_observation_timestamp():
    manager.update([observed_detection], frame_number=10, timestamp=5.0)
    manager.update([predicted_detection], frame_number=11, timestamp=5.5)
    assert manager.active_states[7].last_observation_timestamp == 5.0

def test_prediction_cannot_create_queue_evidence():
    manager.update([observed_detection], frame_number=10, timestamp=5.0)
    for frame in range(11, 30):
        manager.update([predicted_detection], frame_number=frame, timestamp=5.0 + frame / 10)
    assert manager.active_states[7].consecutive_low_motion_frames == 0
    assert manager.active_states[7].is_queued is False
```

- [ ] **Step 3: Run the tests and confirm they fail because prediction metadata is absent and predictions mutate observation state**

Run: `python -m pytest tests/test_runtime_regressions.py -q`

- [ ] **Step 4: Tag observed and predicted detections at their source**

Detector results and `ByteTracker.update()` outputs are `OBSERVED`. `ByteTracker.predict()`
outputs are `PREDICTED`, retain the last observation metadata, and record only the
prediction frame ID for display telemetry.

- [ ] **Step 5: Make VehicleStateManager evidence-aware**

Only observed updates increment confirmation, refresh the last observation, or
modify motion/queue evidence. Predicted updates may return a display detection but
must not mutate observation-backed analytical state. Expiration uses the last real
observation time.

- [ ] **Step 6: Verify smooth continuity and independent trackers**

Add/retain tests proving predicted boxes keep the same track ID, a prediction does
not advance Ultralytics tracker observation state, and north/east/south/west
trackers do not share IDs or state.

- [ ] **Step 7: Run focused and pipeline tests**

Run: `python -m pytest tests/test_runtime_regressions.py tests/test_pipeline_multi_camera.py tests/test_priority_calculator.py -q`

- [ ] **Step 8: Commit observation semantics**

```powershell
git add ai/detection/detection_types.py ai/tracking/byte_tracker.py ai/state/vehicle_state_manager.py ai/pipeline/traffic_pipeline.py ai/visualization/visualizer.py tests/test_runtime_regressions.py tests/test_pipeline_multi_camera.py
git commit -m "fix: separate tracker predictions from observations"
```

### Task 4: Fresh-frame temporal architecture and truthful profile telemetry

**Files:**
- Modify: `server/webrtc_ingest.py`
- Modify: `server/frame_coordinator.py`
- Modify: `server/runtime.py`
- Modify: `server/message_handler.py`
- Modify: `web/schemas.py`
- Modify: `web-ui/src/types/index.ts`
- Test: `tests/test_webrtc_ingest.py`
- Test: `tests/test_frame_coordinator.py`
- Test: `tests/test_runtime_regressions.py`

**Interfaces:**
- Consumes: `ACTIVE_PROFILE.capture_fps`, `webrtc_sample_fps`, `detector_fps`, `preview_fps`, and `batch_size`.
- Produces: `effectiveProfile` telemetry with exact effective values and validation status.
- Preserves: one latest frame per direction and independent per-camera state.

- [ ] **Step 1: Write failing fresh-frame and profile telemetry tests**

```python
async def test_latest_frame_replacement_processes_newest_identity():
    await handler._handle_video_frame(frame("north", "old"))
    await handler._handle_video_frame(frame("north", "new"))
    assert handler.latest_frames["north"]["payload"]["frame_id"] == "new"
    assert len(handler.latest_frames) == 1

def test_runtime_snapshot_publishes_effective_profile():
    profile = runtime_snapshot(ctx)["payload"]["effectiveProfile"]
    assert profile["name"] == "LAPTOP"
    assert profile["batchSize"] == 4
    assert profile["validationStatus"] == "MEASURED_LOCAL_SOFTWARE"
```

- [ ] **Step 2: Run focused tests and confirm missing profile telemetry/configurable sampling failures**

Run: `python -m pytest tests/test_webrtc_ingest.py tests/test_frame_coordinator.py tests/test_runtime_regressions.py -q`

- [ ] **Step 3: Drive WebRTC sampling from the active profile**

Replace the fixed `.25` second interval with `1 / profile.webrtc_sample_fps`.
Continue consuming incoming video into one latest slot so frames never form an
unbounded queue. Keep each peer/direction independent.

- [ ] **Step 4: Use server monotonic receipt time for detector cadence**

Keep client capture timestamps for latency telemetry, but decide whether YOLO is
due using a trusted server monotonic timestamp. Never repeatedly process an old
image; each detector execution consumes the newest available frame identity.

- [ ] **Step 5: Publish effective profile and unknown values honestly**

Expose profile values in health/status telemetry. Use `None`/`UNAVAILABLE` for
unmeasured battery, signal, temperature, latency, or frame age. Do not invent a
30 FPS source rate when it is unknown.

- [ ] **Step 6: Run focused backend and frontend contract checks**

Run: `python -m pytest tests/test_webrtc_ingest.py tests/test_frame_coordinator.py tests/test_runtime_regressions.py tests/test_web_application.py -q`

Run: `cd web-ui; npm run lint; npm run build`

- [ ] **Step 7: Commit temporal/profile telemetry changes**

```powershell
git add server/webrtc_ingest.py server/frame_coordinator.py server/runtime.py server/message_handler.py web/schemas.py web-ui/src/types/index.ts tests/test_webrtc_ingest.py tests/test_frame_coordinator.py tests/test_runtime_regressions.py
git commit -m "fix: publish truthful runtime profile and frame cadence"
```

### Task 5: Hot-path logging, rotation, and runtime exception visibility

**Files:**
- Modify: `ai/utils/logger.py`
- Modify: `server/message_handler.py`
- Modify: `ai/signal/priority_calculator.py`
- Modify: `server/runtime.py`
- Test: `tests/test_runtime_regressions.py`
- Create: `tests/test_operational_logging.py`

**Interfaces:**
- Produces: bounded rotating application/error log handlers using existing log paths.
- Preserves: INFO for lifecycle, connection, disconnection, state changes, errors, and scheduler events.
- Produces: runtime exception counter increment plus concise ERROR log and DEBUG traceback.
- Produces: `log_frame_trace(event: str, **fields) -> None` for DEBUG-only per-frame diagnostics.
- Produces: `run_runtime_iteration(ctx, message_handler, publish=None) -> None`, allowing one real ticker iteration to be tested without running an infinite task.
- Test utility: `failing_runtime_iteration` invokes `run_runtime_iteration` with a real context and a pipeline double whose only external action raises `ValueError("test failure")`.

- [ ] **Step 1: Write failing logging-level and exception-visibility tests**

```python
def test_frame_trace_messages_are_debug_not_info(caplog):
    with caplog.at_level(logging.DEBUG, logger="MessageHandler"):
        log_frame_trace("YOLO_START", frame_id="north-1", direction="north")
    record = next(record for record in caplog.records if "YOLO_START" in record.message)
    assert record.levelno == logging.DEBUG

async def test_runtime_ticker_logs_exception_and_continues(caplog, failing_runtime_iteration):
    await failing_runtime_iteration()
    assert ctx.frame_processing_errors == 1
    assert any(record.levelno == logging.ERROR and "Runtime ticker failed" in record.message for record in caplog.records)

def test_file_handlers_are_rotating_and_bounded():
    logger = get_logger("rotation-test")
    handlers = [handler for handler in logger.handlers if isinstance(handler, RotatingFileHandler)]
    assert handlers and handlers[0].maxBytes > 0 and handlers[0].backupCount > 0
```

- [ ] **Step 2: Run logging tests and confirm frame traces are INFO, rotation is absent, and ticker failures are silent**

Run: `python -m pytest tests/test_operational_logging.py tests/test_runtime_regressions.py -q`

- [ ] **Step 3: Move repetitive frame/ranking logs to DEBUG**

Keep connection and scheduler state transitions at INFO. Do not remove diagnostic
content; make it opt-in through DEBUG.

- [ ] **Step 4: Add bounded rotation through the existing logger factory**

Use `logging.handlers.RotatingFileHandler` with environment-bounded maximum bytes
and backup count. Avoid adding duplicate handlers on repeated logger construction.

- [ ] **Step 5: Make runtime ticker failures visible without losing fault tolerance**

On unexpected exceptions, increment the existing error counter, log exception type
and concise message at ERROR, emit traceback at DEBUG, and continue only when safe.

- [ ] **Step 6: Run focused and full tests**

Run: `python -m pytest tests/test_operational_logging.py tests/test_runtime_regressions.py -q`

- [ ] **Step 7: Commit operational diagnostics**

```powershell
git add ai/utils/logger.py server/message_handler.py ai/signal/priority_calculator.py server/runtime.py tests/test_operational_logging.py tests/test_runtime_regressions.py
git commit -m "fix: bound logs and expose runtime failures"
```

### Task 6: Final verification and remediation report

**Files:**
- Create: `docs/SIH_CRITICAL_CORRECTNESS_REMEDIATION_2026-09-10.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: exact test/build output and the final Git diff.
- Produces: P0/P1 matrices, file/change/reason/test mapping, test inventory, hardware/observation/NCNN verification, and remaining limitations.

- [ ] **Step 1: Run the complete backend verification**

Run: `python -m pytest -q --timeout=60`

Run: `python -m compileall -q ai server web startup core shared config scripts tests`

Run: `python -m pip check`

- [ ] **Step 2: Run complete frontend verification**

Run: `cd web-ui; npm run lint; npm run build; npm audit`

- [ ] **Step 3: Run the integrated four-camera smoke test**

Start the combined server locally, wait for model warm-up, run
`python scripts/smoke_runtime.py`, and stop the exact server process cleanly.

- [ ] **Step 4: Review the final diff against every attachment requirement**

Confirm no forced hardware simulation, no constant hardware capability, no NCNN
batch-four warm-up, no predicted observation mutation, no unbounded frame queue,
no tracker sharing, no repetitive frame INFO messages, no silent ticker exception,
and no fabricated telemetry.

- [ ] **Step 5: Write the evidence-based remediation report**

Record exact commands and results. Explicitly retain limitations: Raspberry Pi
profile unvalidated, traffic accuracy unmeasured, physical ESP32 untested,
emergency recognition absent, and public-road readiness not claimed.

- [ ] **Step 6: Verify documentation and repository cleanliness**

Run: `git diff --check`

Run: `git status --short --branch`

- [ ] **Step 7: Commit the final report**

```powershell
git add README.md docs/SIH_CRITICAL_CORRECTNESS_REMEDIATION_2026-09-10.md
git commit -m "docs: report SIH correctness remediation"
```

- [ ] **Step 8: Push the requested branch after verifying local and remote commit identity**

```powershell
git push origin codex/four-lane-video
git rev-parse HEAD
git rev-parse origin/codex/four-lane-video
```
