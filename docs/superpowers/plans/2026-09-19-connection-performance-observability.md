# Connection, Performance, and Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make camera ownership/reconnect deterministic, keep multi-camera processing fresh and fair, and expose enough timing evidence to select a low-latency laptop inference strategy.

**Architecture:** Add generation-safe session and connection ownership, derive camera lifecycle from independently tracked signalling/media/frame/inference facts, and move frame-slot accounting into a focused coordinator abstraction. Carry a typed per-frame timing record through decoding, inference, analytics, scheduling, and publication; use measured benchmarks to choose the laptop batch default without changing YOLOv8n accuracy settings.

**Tech Stack:** Python/FastAPI/asyncio/aiortc/pytest, React/Vite/TypeScript, Expo/React Native WebRTC, PowerShell benchmark entry points.

**Spec:** `docs/superpowers/specs/2026-09-19-laptop-first-portable-validation-design.md`

## Global Constraints

- Preserve protocol `1.0`; additions to payloads must remain optional for old clients.
- Keep WebRTC and JPEG paths feeding the same bounded latest-frame coordinator.
- A registered socket without fresh usable media and processing is not `LIVE`.
- Stale/dropped frames never create zero traffic observations.
- Do not change confidence, IoU, input resolution, or model identity for performance results.
- Numeric release targets are recorded only after the corrected baseline is measured.

## Review Focus

- Old-socket disconnect racing a reconnect must not delete the new generation; Task 1 tests socket/generation conditional removal.
- A conflicting node must not displace a healthy owner, while an expired/dead owner becomes reclaimable; Task 2 tests both boundaries.
- Continuous frames from one direction must not starve another; Task 3 tests round-robin selection under replacement.
- Invalid/skewed client timestamps must not create negative or trusted network latency; Task 4 tests unavailable arrival age.
- Unsupported WebRTC statistics must remain null/`unavailable`; Task 5 tests sparse stats reports.

---

### Task 1: Generation-Safe Session and Connection Ownership

**Files:**
- Modify: `server/session_manager.py`
- Modify: `server/connection_manager.py`
- Test: `tests/test_session_ownership.py`

**Interfaces:**
- Produces: `NodeSession.generation: str`, `NodeSession.transport_alive: bool`, `SessionManager.remove_session(node_id, generation=None) -> Optional[NodeSession]`.
- Produces: `ConnectionLease(node_id, generation, websocket)` and `ConnectionManager.disconnect(node_id, generation=None, websocket=None) -> bool`.
- Consumed by: Task 2 registration/disconnect logic and WebRTC cleanup.

- [ ] **Step 1: Write failing generation and conditional-cleanup tests**

```python
def test_old_generation_cannot_remove_reconnected_session():
    sessions = SessionManager(timeout_sec=10)
    old = sessions.create_session("cam-n", "north")
    new = sessions.replace_session("cam-n", "north", reconnect_token=old.session_token)
    assert sessions.remove_session("cam-n", generation=old.generation) is None
    assert sessions.get_session("cam-n") is new

@pytest.mark.asyncio
async def test_old_socket_disconnect_cannot_remove_new_connection():
    manager = ConnectionManager()
    await manager.connect("cam-n", old_ws, generation="g1")
    await manager.connect("cam-n", new_ws, generation="g2")
    assert await manager.disconnect("cam-n", generation="g1", websocket=old_ws) is False
    assert manager.get_connection("cam-n") is new_ws
```

- [ ] **Step 2: Run tests and confirm the missing generation API fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_session_ownership.py -q`

Expected: FAIL because `replace_session`, `generation`, and conditional disconnect do not exist.

- [ ] **Step 3: Implement immutable ownership generations**

```python
@dataclass
class ConnectionLease:
    node_id: str
    generation: str
    websocket: WebSocket

def remove_session(self, node_id: str, generation: str | None = None):
    current = self.sessions.get(node_id)
    if current is None or (generation is not None and current.generation != generation):
        return None
    return self.sessions.pop(node_id)
```

Create each accepted registration with `generation=uuid.uuid4().hex`; close old resources by their generation and never by node ID alone after a reconnect.

- [ ] **Step 4: Run focused and existing communication tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_session_ownership.py tests/test_communication_server.py tests/test_runtime_regressions.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add server/session_manager.py server/connection_manager.py tests/test_session_ownership.py
git commit -m "fix: make camera ownership cleanup generation safe"
```

### Task 2: Truthful Lifecycle, Reconnect, and Takeover Policy

**Files:**
- Create: `server/camera_lifecycle.py`
- Modify: `server/message_handler.py`
- Modify: `server/webrtc_ingest.py`
- Modify: `web/services/node_service.py`
- Modify: `server/protocol.py`
- Modify: `C:/Users/ashek/Desktop/traffic-camera-app/src/services/connection/WebSocketConnectionService.ts`
- Test: `tests/test_camera_lifecycle.py`
- Test: `tests/test_communication_server.py`
- Test: `C:/Users/ashek/Desktop/traffic-camera-app/scripts/test-regressions.cjs`

**Interfaces:**
- Consumes: generation-aware session/connection operations from Task 1.
- Produces: `CameraLifecycleState` enum and `CameraStatusSnapshot.to_dict()`.
- Produces: structured `DIRECTION_OCCUPIED` payload `{direction, owner_state, retry_after_ms}`.

- [ ] **Step 1: Write failing lifecycle and takeover tests**

```python
def test_authenticated_socket_without_media_is_connecting():
    status = CameraStatusSnapshot(authenticated=True, media_connected=False)
    assert status.state is CameraLifecycleState.CONNECTING

async def test_dead_owner_is_reclaimable_after_grace(handler, clock):
    first = await register(handler, "old", "north", old_ws)
    handler.handle_connection_loss("old", websocket=old_ws)
    clock.advance(handler.takeover_grace_sec + 0.01)
    second = await register(handler, "new", "north", new_ws)
    assert second["type"] == "REGISTRATION_ACK"

async def test_live_owner_conflict_has_retry_details(handler):
    response = await register_conflict(handler, "north")
    assert response["payload"]["code"] == "DIRECTION_OCCUPIED"
    assert response["payload"]["retry_after_ms"] > 0
```

- [ ] **Step 2: Run the focused tests to establish failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_camera_lifecycle.py tests/test_communication_server.py -q`

Expected: FAIL because lifecycle facts, grace policy, and retry details are absent.

- [ ] **Step 3: Implement lifecycle derivation and takeover without protocol replacement**

```python
class CameraLifecycleState(str, Enum):
    OFFLINE = "OFFLINE"
    PAIRING = "PAIRING"
    CONNECTING = "CONNECTING"
    LIVE = "LIVE"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    RECONNECTING = "RECONNECTING"

def derive_state(self, now: float) -> CameraLifecycleState:
    if self.error_code: return CameraLifecycleState.ERROR
    if self.reconnecting: return CameraLifecycleState.RECONNECTING
    if not self.authenticated: return CameraLifecycleState.PAIRING if self.pairing_active else CameraLifecycleState.OFFLINE
    if not self.media_connected or self.last_frame_at is None: return CameraLifecycleState.CONNECTING
    if now - self.last_inference_at > self.inference_fresh_sec: return CameraLifecycleState.DEGRADED
    return CameraLifecycleState.LIVE
```

Use the same valid session token for same-node reconnect; permit a different paired node only after transport death plus configured grace. Consume pairing credentials only after registration succeeds.

- [ ] **Step 4: Make mobile teardown graceful and preserve automatic reconnect**

Add an awaited `disconnect(reason, { preserveReconnectIdentity: boolean })`; send `DISCONNECT` before closing when the user stops, but preserve token/QR identity for unexpected network reconnects. Extend the Node test script to assert one graceful message and no duplicate reconnect timer.

- [ ] **Step 5: Run cross-repository tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_camera_lifecycle.py tests/test_communication_server.py tests/test_webrtc_ingest.py tests/test_system_contract.py -q
Push-Location ..\traffic-camera-app; npm test; npm run type-check; Pop-Location
```

Expected: PASS.

- [ ] **Step 6: Commit both repositories separately**

```powershell
git add server/camera_lifecycle.py server/message_handler.py server/webrtc_ingest.py server/protocol.py web/services/node_service.py tests
git commit -m "fix: make camera lifecycle and takeover truthful"
Push-Location ..\traffic-camera-app
git add src/services/connection/WebSocketConnectionService.ts scripts/test-regressions.cjs
git commit -m "fix: preserve reconnect identity during graceful cleanup"
Pop-Location
```

### Task 3: Bounded Fair Frame Slots

**Files:**
- Create: `server/frame_slots.py`
- Modify: `server/message_handler.py`
- Modify: `server/frame_coordinator.py`
- Modify: `core/application_context.py`
- Test: `tests/test_frame_slots.py`
- Test: `tests/test_frame_coordinator.py`

**Interfaces:**
- Produces: `LatestFrameSlots.offer(direction, packet) -> Optional[packet]` and `select_due(now, directions) -> list[packet]`.
- Produces: `FrameCounters(offered, selected, processed, replaced, stale_dropped, decode_failed, inference_failed)` per direction.

- [ ] **Step 1: Write boundedness and round-robin failure tests**

```python
def test_each_direction_keeps_exactly_one_pending_packet():
    slots = LatestFrameSlots(DIRECTIONS)
    for sequence in range(100):
        slots.offer("north", packet(sequence))
    assert slots.pending_count == 1
    assert slots.counters["north"].offered == 100
    assert slots.counters["north"].replaced == 99

def test_busy_north_does_not_starve_other_due_directions():
    slots = LatestFrameSlots(DIRECTIONS)
    selected = []
    for tick in range(12):
        slots.offer("north", packet(tick))
        slots.offer(DIRECTIONS[tick % 4], packet(tick))
        selected.extend(p["payload"]["direction"] for p in slots.select_due(tick, DIRECTIONS))
    assert set(selected) == set(DIRECTIONS)
```

- [ ] **Step 2: Run tests and confirm current dictionary API fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_frame_slots.py tests/test_frame_coordinator.py -q`

- [ ] **Step 3: Implement slots with lock-protected offer and round-robin cursor**

```python
class LatestFrameSlots:
    def offer(self, direction: str, packet: dict) -> dict | None:
        previous = self._pending.get(direction)
        self._pending[direction] = packet
        self.counters[direction].offered += 1
        if previous is not None:
            self.counters[direction].replaced += 1
        return previous

    def select_due(self, now: float, max_items: int) -> list[dict]:
        ordered = self._directions[self._cursor:] + self._directions[:self._cursor]
        selected = [self._pending.pop(direction) for direction in ordered
                    if direction in self._pending][:max_items]
        if selected:
            last = selected[-1]["payload"]["direction"]
            self._cursor = (self._directions.index(last) + 1) % len(self._directions)
            for packet in selected:
                self.counters[packet["payload"]["direction"]].selected += 1
        return selected

    def mark_processed(self, direction: str) -> None:
        self.counters[direction].processed += 1

    def mark_failure(self, direction: str, stage: str) -> None:
        field = "decode_failed" if stage == "decode" else "inference_failed"
        setattr(self.counters[direction], field, getattr(self.counters[direction], field) + 1)
```

Selection starts after the last selected direction, returns only current fresh packets, and never reports a drop as an empty observation.

- [ ] **Step 4: Integrate JPEG and decoded WebRTC submission through the same slots**

Replace `handler.latest_frames` mutation with `handler.frame_slots.offer(direction, raw_json)`; publish per-direction counters through runtime telemetry.

- [ ] **Step 5: Run focused, safety, and observation tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_frame_slots.py tests/test_frame_coordinator.py tests/test_observation_semantics.py tests/test_safety_invariants.py -q`

- [ ] **Step 6: Commit**

```powershell
git add server/frame_slots.py server/frame_coordinator.py server/message_handler.py core/application_context.py tests/test_frame_slots.py tests/test_frame_coordinator.py
git commit -m "perf: add bounded fair per-camera frame slots"
```

### Task 4: Per-Frame Stage Timing

**Files:**
- Create: `server/frame_timing.py`
- Modify: `server/frame_coordinator.py`
- Modify: `server/message_handler.py`
- Modify: `ai/pipeline/traffic_pipeline.py`
- Modify: `server/runtime.py`
- Modify: `web-ui/src/types/index.ts`
- Modify: `web-ui/src/features/dashboard/useDashboardViewModel.ts`
- Modify: `web-ui/src/shared/components/scada/MetricStrip.tsx`
- Test: `tests/test_frame_timing.py`

**Interfaces:**
- Produces: `FrameTiming.mark(stage, monotonic=None, wall_ms=None)` and `FrameTiming.to_metrics(publication_monotonic) -> dict`.
- Produces optional telemetry keys `decode_ms`, `coordinator_wait_ms`, `inference_ms`, `tracking_ms`, `analytics_ms`, `scheduler_ms`, `publication_ms`, `server_total_ms`, `arrival_age_ms`, `frame_age_ms`.

- [ ] **Step 1: Write timing math and clock-trust tests**

```python
def test_stage_durations_use_monotonic_clock():
    timing = FrameTiming(received_monotonic=10.0)
    timing.mark("decoded", monotonic=10.010)
    timing.mark("selected", monotonic=10.025)
    timing.mark("inference_end", monotonic=10.125)
    metrics = timing.to_metrics(publication_monotonic=10.150)
    assert metrics["decode_ms"] == pytest.approx(10)
    assert metrics["coordinator_wait_ms"] == pytest.approx(15)
    assert metrics["server_total_ms"] == pytest.approx(150)

def test_untrusted_capture_clock_reports_arrival_age_unavailable():
    assert FrameTiming(capture_wall_ms=float("nan")).to_metrics(2.0)["arrival_age_ms"] is None
```

- [ ] **Step 2: Run tests and verify failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_frame_timing.py -q`

- [ ] **Step 3: Implement timing object and thread it through existing calls**

Use monotonic values for server stage deltas. Report capture/arrival age only when the capture timestamp is finite and within the configured skew tolerance; retain `None` otherwise. Do not subtract phone and server clocks blindly.

- [ ] **Step 4: Expose typed dashboard stage metrics**

```ts
export interface PipelineStageLatency {
  transportMs: number | null;
  decodeMs: number;
  queueWaitMs: number;
  inferenceMs: number;
  postProcessingMs: number;
  totalMs: number;
  frameAgeMs: number;
}
```

Render unavailable transport values as `—`, not zero.

- [ ] **Step 5: Run backend and UI verification**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_frame_timing.py tests/test_e2e_pipeline_websocket.py tests/test_web_application.py -q
Push-Location web-ui; npm run build; Pop-Location
```

- [ ] **Step 6: Commit**

```powershell
git add server/frame_timing.py server/frame_coordinator.py server/message_handler.py server/runtime.py ai/pipeline/traffic_pipeline.py web-ui/src tests/test_frame_timing.py
git commit -m "feat: expose per-stage frame latency"
```

### Task 5: WebRTC Statistics and Actual Transport Identity

**Files:**
- Modify: `C:/Users/ashek/Desktop/traffic-camera-app/src/services/camera/WebRTCVideoSession.ts`
- Modify: `C:/Users/ashek/Desktop/traffic-camera-app/src/types/protocol.ts`
- Modify: `server/protocol.py`
- Modify: `server/message_handler.py`
- Modify: `server/runtime.py`
- Modify: `web-ui/src/shared/components/scada/DashboardLayout.tsx`
- Modify: `web-ui/src/types/index.ts`
- Test: `C:/Users/ashek/Desktop/traffic-camera-app/scripts/test-webrtc.cjs`
- Test: `tests/test_webrtc_stats.py`

**Interfaces:**
- Produces optional protocol message `WEBRTC_STATS` containing nullable standardized fields.
- Produces lane telemetry `transport: "webrtc" | "jpeg-json" | "local"` and `transportStats`.

- [ ] **Step 1: Add sparse-stat parsing tests on mobile and backend**

```javascript
assert.deepStrictEqual(normalizeWebRTCStats([{type:'outbound-rtp', kind:'video', framesPerSecond:8}]), {
  sentFps: 8, packetsLost: null, jitterMs: null, frameWidth: null, frameHeight: null,
  encodeMsPerFrame: null, jitterBufferDelayMs: null
});
```

```python
def test_missing_webrtc_stats_remain_none():
    parsed = WebRTCStatsPayload.model_validate({"sent_fps": 8})
    assert parsed.packet_loss is None
```

- [ ] **Step 2: Run both tests and verify failure**

Run backend and `node scripts/test-webrtc.cjs`; expect missing normalizer/schema failures.

- [ ] **Step 3: Poll `RTCPeerConnection.getStats()` at one-second cadence**

Compute rates from counter deltas, guard counter resets, send only bounded numeric nullable fields, and stop the timer with the peer connection.

- [ ] **Step 4: Store stats only for the authenticated current generation**

Reject mismatched direction/node/session ownership exactly like frames. Publish the actual `source_kind`; replace the hard-coded `JPEG samples` dashboard copy with data-derived transport labels.

- [ ] **Step 5: Run contract, mobile, and UI tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_webrtc_stats.py tests/test_system_contract.py -q
Push-Location ..\traffic-camera-app; npm test; npm run type-check; Pop-Location
Push-Location web-ui; npm run build; Pop-Location
```

- [ ] **Step 6: Commit both repositories**

Commit backend/UI as `feat: report WebRTC transport health`; commit mobile as `feat: publish standardized WebRTC statistics`.

### Task 6: Explicit Readiness and Measured Warm-Up

**Files:**
- Create: `ai/models/readiness.py`
- Modify: `ai/models/model_manager.py`
- Modify: `core/application_context.py`
- Modify: `web/routes/api_routes.py`
- Modify: `web/schemas.py`
- Test: `tests/test_model_readiness.py`
- Modify: `scripts/benchmark_inference.py`

**Interfaces:**
- Produces: `ReadinessSnapshot(process_started, model_loaded, model_warmed, camera_service_ready, scheduler_ready, failure)`.
- Produces: `WarmupMetrics(load_ms, first_inference_ms, second_inference_ms, warm_p50_ms, warm_p95_ms, trials)`.

- [ ] **Step 1: Write readiness transition and failed-warmup tests**

```python
def test_full_readiness_requires_model_warmup_and_services():
    ready = ReadinessSnapshot(process_started=True, model_loaded=True, model_warmed=False,
                              camera_service_ready=True, scheduler_ready=True)
    assert ready.fully_ready is False

def test_failed_warmup_is_visible_and_blocks_readiness(fake_yolo):
    fake_yolo.predict.side_effect = RuntimeError("warmup failed")
    with pytest.raises(RuntimeError):
        ModelManager(model_factory=lambda _: fake_yolo)
```

- [ ] **Step 2: Run tests and verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_model_readiness.py -q`

- [ ] **Step 3: Separate load and warm-up measurements without hiding cold inference**

Warm-up executes first inference, second inference, then a configurable small steady sample. Readiness changes are explicit and the health endpoint reports stages plus failure. Production still refuses frames until warm-up completes.

- [ ] **Step 4: Extend benchmark output**

Write JSON containing load, first, second, warm p50/p95, model SHA-256, commit, profile, input, batch, device, Python/OS/CPU, and trial count.

- [ ] **Step 5: Run readiness tests and a short benchmark**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_model_readiness.py tests/test_runtime_regressions.py -q
.\.venv\Scripts\python.exe scripts/benchmark_inference.py --model yolov8n.pt --input-size 576 --trials 10 --output docs/benchmarks/warmup-baseline.json
```

- [ ] **Step 6: Commit**

```powershell
git add ai/models/readiness.py ai/models/model_manager.py core/application_context.py web scripts/benchmark_inference.py tests/test_model_readiness.py docs/benchmarks/warmup-baseline.json
git commit -m "feat: gate readiness on measured model warmup"
```

### Task 7: Evidence-Based Batching and Multi-Camera Benchmark

**Files:**
- Modify: `config/deployment.py`
- Modify: `server/frame_coordinator.py`
- Create: `scripts/benchmark_multicamera.py`
- Create: `tests/test_inference_policy.py`
- Modify: `docs/PERFORMANCE_AUDIT.md`

**Interfaces:**
- Produces: `InferencePolicy(mode: Literal["single", "micro_batch"], max_batch_size: int, collection_window_ms: int)` from deployment profile.
- Produces machine-readable 1/2/3/4-camera trial artifacts.

- [ ] **Step 1: Write policy tests that prohibit unmeasured implicit batching**

```python
def test_laptop_latency_profile_defaults_to_single_frame():
    profile = load_deployment_profile({"TRAFFIC_PROFILE": "laptop"})
    assert profile.inference_policy.mode == "single"
    assert profile.inference_policy.max_batch_size == 1

def test_micro_batch_is_explicit_and_bounded():
    profile = load_deployment_profile({"TRAFFIC_PROFILE":"laptop", "YOLO_BATCH_SIZE":"2"})
    assert profile.inference_policy.max_batch_size == 2
```

- [ ] **Step 2: Run the test and confirm the current batch-4 default fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_inference_policy.py tests/test_deployment_profile.py -q`

- [ ] **Step 3: Implement explicit policy and benchmark runner**

The runner replays identical source frames for batch 1, 2, and current 4; records p50/p95 inference, queue, server total, frame age, per-camera processed/replaced/stale counts, CPU, RSS, model hash, and environment. It must not modify thresholds or input size between trials.

- [ ] **Step 4: Run corrected baseline and select configuration from evidence**

```powershell
.\.venv\Scripts\python.exe scripts/benchmark_multicamera.py --cameras 1,2,3,4 --batch-sizes 1,2,4 --input-size 576 --duration 30 --output docs/benchmarks/multicamera-corrected-baseline.json
```

Expected: artifact is complete. Set laptop default to the lowest p95 frame-age policy that keeps all cameras progressing; do not assert a number before this run.

- [ ] **Step 5: Run regression and model structural check**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_inference_policy.py tests/test_batch_detection.py tests/test_model_regression.py tests/test_frame_coordinator.py -q`

- [ ] **Step 6: Commit**

```powershell
git add config/deployment.py server/frame_coordinator.py scripts/benchmark_multicamera.py tests/test_inference_policy.py docs/PERFORMANCE_AUDIT.md docs/benchmarks/multicamera-corrected-baseline.json
git commit -m "perf: select laptop inference policy from latency evidence"
```

### Task 8: Adaptive Cadence Decision Gate and Phase Verification

**Files:**
- Create if beneficial: `server/adaptive_cadence.py`
- Modify if beneficial: `config/deployment.py`
- Modify if beneficial: `server/frame_coordinator.py`
- Create: `tests/test_adaptive_cadence.py`
- Create: `docs/benchmarks/connection-performance-phase.json`
- Modify: `docs/RELIABILITY_AUDIT.md`
- Modify: `docs/PERFORMANCE_AUDIT.md`

**Interfaces:**
- Optional output: `AdaptiveCadence.update(service_ms, frame_age_ms, active_cameras, overloaded) -> float`.
- Always outputs a documented evidence decision: enabled with comparison, or disabled because no benefit was measured.

- [ ] **Step 1: Write deterministic bounds/recovery tests before enabling**

```python
def test_cadence_decreases_on_sustained_overload_and_recovers():
    ctl = AdaptiveCadence(min_fps=.5, max_fps=2.0, initial_fps=2.0, window=3)
    overloaded = [ctl.update(700, 1500, 4, True) for _ in range(3)]
    recovered = [ctl.update(100, 150, 1, False) for _ in range(6)]
    assert min(overloaded) >= .5
    assert recovered[-1] == 2.0
```

- [ ] **Step 2: Compare fixed versus adaptive cadence using identical inputs**

Run the multi-camera benchmark with fixed cadence, then with the proposed controller. Record frame-age distribution, fairness, processed observations, CPU, RSS, and count stability.

- [ ] **Step 3: Apply the evidence gate**

Enable only when p95 frame age improves without starvation or count-regression breach. Otherwise delete the implementation/test files and record `adaptive_cadence: rejected` with measured reasons in the artifact.

- [ ] **Step 4: Run the complete phase verification**

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Push-Location web-ui; npm run build; Pop-Location
Push-Location ..\traffic-camera-app; npm test; npm run type-check; Pop-Location
```

Expected: backend 153 baseline tests plus new tests pass; UI and mobile checks pass.

- [ ] **Step 5: Commit the decision and evidence**

```powershell
git add server config tests docs/benchmarks/connection-performance-phase.json docs/RELIABILITY_AUDIT.md docs/PERFORMANCE_AUDIT.md
git commit -m "test: validate connection and multi-camera performance phase"
```
