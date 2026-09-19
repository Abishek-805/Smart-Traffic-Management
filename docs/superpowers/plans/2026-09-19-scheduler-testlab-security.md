# Scheduler, Test Lab, and Security Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make scheduler decisions auditable, validate emergency behavior through authenticated simulation, and provide repeatable replay/load/impairment/soak/security evidence.

**Architecture:** Add versioned event and decision-record contracts around the existing scheduler instead of altering safety logic. Extend the current replay lab with a controllable clock and structural artifacts, add an application-boundary camera impairment harness, and harden existing pairing/message paths with bounded replay and rate-limit services.

**Tech Stack:** Python/FastAPI/asyncio/Pydantic/pytest, React/Vite/TypeScript, JSONL/JSON evidence.

**Spec:** `docs/superpowers/specs/2026-09-19-laptop-first-portable-validation-design.md`

## Global Constraints

- Emergency input in this plan is simulated and authenticated.
- Preserve minimum/maximum green, yellow/all-red clearance, fairness, and fail-safe behavior.
- Replays use the production normalization/inference/tracking/analytics/scheduler path where the scenario provides frames.
- Security defaults may support local development but cannot silently weaken production mode.
- Logs must not contain tokens, pairing secrets, or raw credentials.

## Review Focus

- Two simultaneous emergency events must resolve deterministically without skipping safe clearance; Task 1 pins this.
- Decision alternatives must include excluded stale lanes and their exclusion reason; Task 2 pins this.
- Replay with the same seed/config/input must be byte-stable after volatile metadata normalization; Task 3 pins this.
- A reconnect storm must remain bounded and recover without starving healthy lanes; Task 4 pins this.
- Rate limits must not permit node-ID rotation to bypass a global/IP budget; Task 5 pins this.

---

### Task 1: Authenticated Simulated Emergency Lifecycle

**Files:**
- Create: `ai/signal/emergency_event.py`
- Modify: `ai/signal/emergency_override.py`
- Modify: `ai/pipeline/traffic_pipeline.py`
- Modify: `web/routes/api_routes.py`
- Modify: `web/schemas.py`
- Create: `tests/test_emergency_lifecycle.py`

**Interfaces:**
- Produces: `EmergencyEvent(event_id, direction, source="simulation", issued_at, expires_at, authenticated_actor)`.
- Produces: `EmergencyEventStore.activate`, `expire`, `active_events`, and bounded audit records.

- [ ] **Step 1: Write failing lifecycle and conflict tests**

```python
def test_emergency_expires_and_normal_fairness_resumes(fake_clock):
    store.activate(event("south", expires_at=15))
    assert scheduler.choose(snapshot_at(10)).direction == "south"
    fake_clock.set(16)
    assert scheduler.choose(snapshot_at(16)).reason != "EMERGENCY"

def test_conflicting_events_use_oldest_then_safe_transition():
    store.activate(event("south", issued_at=10))
    store.activate(event("east", issued_at=11))
    decisions = run_until_both_served()
    assert_safe_clearance(decisions)
    assert emergency_order(decisions) == ["south", "east"]
```

- [ ] **Step 2: Run test and verify failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_emergency_lifecycle.py -q`

- [ ] **Step 3: Implement event store and operator-protected simulation endpoint**

Use the existing operator authorization dependency. Reject past expiry, unsupported directions, duplicate IDs with different payloads, and unauthenticated requests. The dashboard payload must say `SIMULATED EMERGENCY EVENT`.

- [ ] **Step 4: Run emergency and safety suites**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_emergency_lifecycle.py tests/test_emergency_override.py tests/test_signal_scheduler.py tests/test_safety_invariants.py -q`

- [ ] **Step 5: Commit**

Commit as `feat: validate authenticated simulated emergency lifecycle`.

### Task 2: Versioned Scheduler Decision Records and Dashboard Explanation

**Files:**
- Create: `ai/signal/decision_record.py`
- Modify: `ai/signal/signal_scheduler.py`
- Modify: `ai/pipeline/traffic_pipeline.py`
- Modify: `ai/logging/decision_history.py`
- Modify: `server/runtime.py`
- Modify: `web-ui/src/types/index.ts`
- Modify: `web-ui/src/features/dashboard/useDashboardViewModel.ts`
- Create: `web-ui/src/shared/components/scada/DecisionExplanation.tsx`
- Create: `tests/test_decision_records.py`

**Interfaces:**
- Produces: `DecisionRecordV1(reason_code, selected, inputs, alternatives, constraints, freshness, emergency, config_revision, timestamp)`.

- [ ] **Step 1: Write failing complete-record tests**

```python
def test_record_explains_selected_and_stale_alternatives():
    record = build_record(snapshot_with_stale_east())
    assert record.reason_code == "HIGHEST_DEMAND_SCORE"
    assert record.selected.direction == "south"
    east = next(a for a in record.alternatives if a.direction == "east")
    assert east.eligible is False
    assert east.exclusion_reason == "STALE_OBSERVATION"
    assert record.constraints.minimum_green_sec > 0
```

- [ ] **Step 2: Run test and verify missing record fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_decision_records.py -q`

- [ ] **Step 3: Implement record construction at the scheduler boundary**

```python
@dataclass(frozen=True)
class DecisionAlternative:
    direction: str
    score: float | None
    eligible: bool
    freshness_ms: float | None
    exclusion_reason: str | None
```

Store bounded history and config revision; keep reason codes stable even when display wording changes.

- [ ] **Step 4: Render “Why was this approach selected?”**

The component shows selected direction, reason, demand inputs, freshness, constraints, emergency state, and alternative exclusions. Missing values render `Unavailable`.

- [ ] **Step 5: Run scheduler, API, and UI checks**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_decision_records.py tests/test_signal_scheduler.py tests/test_web_application.py -q
Push-Location web-ui; npm run build; Pop-Location
```

- [ ] **Step 6: Commit**

Commit as `feat: explain every scheduler decision`.

### Task 3: Deterministic Production-Path Replay

**Files:**
- Modify: `ai/pipeline/replay_lab.py`
- Create: `ai/pipeline/replay_clock.py`
- Create: `scripts/run_replay.py`
- Create: `tests/fixtures/replay/golden-scenarios.json`
- Modify: `tests/test_traffic_replay_lab.py`
- Create: `tests/test_replay_determinism.py`

**Interfaces:**
- Produces: `ReplayClock.now()/monotonic()/advance()` and `ReplayRunResult.to_evidence()`.
- Produces scenarios for congestion change, empty/stale lanes, fairness, max wait, emergency, reconnect, malformed frame, portrait, and landscape.

- [ ] **Step 1: Write failing repeatability and scenario coverage tests**

```python
def test_same_seed_and_config_produce_same_structural_evidence():
    first = run_golden(seed=42).normalized_json()
    second = run_golden(seed=42).normalized_json()
    assert first == second

@pytest.mark.parametrize("name", REQUIRED_GOLDEN_SCENARIOS)
def test_required_scenario_exists(name):
    assert name in load_scenarios()
```

- [ ] **Step 2: Run tests and verify current replay gaps**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_traffic_replay_lab.py tests/test_replay_determinism.py -q`

- [ ] **Step 3: Inject the replay clock and structural normalization**

Do not monkeypatch global time inside production modules; pass the clock to replay-owned orchestration and scheduler seams. Normalize volatile wall timestamps while preserving relative timing and decision order.

- [ ] **Step 4: Generate golden evidence and compare**

Run: `.\.venv\Scripts\python.exe scripts/run_replay.py --scenarios tests/fixtures/replay/golden-scenarios.json --seed 42 --output docs/benchmarks/replay-golden.json`

- [ ] **Step 5: Commit**

Commit as `test: add deterministic traffic replay evidence`.

### Task 4: Multi-Camera Impairment, Resource Pressure, and Soak Harness

**Files:**
- Create: `testing/camera_simulator.py`
- Create: `testing/resource_sampler.py`
- Create: `scripts/run_multicamera_lab.py`
- Create: `scripts/run_soak.py`
- Create: `tests/test_camera_simulator.py`
- Create: `tests/test_short_soak.py`
- Modify: `docs/TEST_STRATEGY.md`

**Interfaces:**
- Produces: `CameraProducerConfig(direction, resolution, orientation, fps, burst, delay_ms, jitter_ms, loss, disconnect_at, reconnect_after, corruption, reorder_window)`.
- Produces bounded JSON evidence with per-camera progress and process resource series.

- [ ] **Step 1: Write failing impairment and bounded-memory unit tests**

```python
def test_seeded_simulator_reproduces_delay_loss_and_reordering():
    assert simulate(CONFIG, seed=7) == simulate(CONFIG, seed=7)

async def test_reconnect_storm_keeps_slots_bounded_and_healthy_lane_progressing():
    result = await lab.run(cameras=[flapping("north"), healthy("south")], duration=5)
    assert result.max_pending_per_direction == 1
    assert result.processed["south"] > 0
    assert result.backend_restarts == 0
```

- [ ] **Step 2: Run tests and verify harness is absent**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_camera_simulator.py tests/test_short_soak.py -q`

- [ ] **Step 3: Implement application-boundary impairments and resource sampling**

Use seeded scheduling, bounded corruption payloads, and psutil for CPU/RSS/thread counts. Record the limitation that this does not reproduce real RTP impairment. Long soak defaults to local/manual; CI short soak remains under two minutes.

- [ ] **Step 4: Run 1–4 camera and short soak evidence**

```powershell
.\.venv\Scripts\python.exe scripts/run_multicamera_lab.py --cameras 1,2,3,4 --duration 30 --output docs/benchmarks/multicamera-impairment.json
.\.venv\Scripts\python.exe scripts/run_soak.py --duration 90 --output docs/benchmarks/short-soak.json
```

- [ ] **Step 5: Document resource-constrained Windows procedure**

Document processor-affinity and memory-observation commands as resource-pressure tests, never Pi benchmarks. The harness records whether constraints were actually applied.

- [ ] **Step 6: Run tests and commit**

Run the new tests plus frame/safety/runtime tests; commit as `test: add multi-camera impairment and soak lab`.

### Task 5: Pairing Replay Protection, Validation, Rate Limits, and Audit Events

**Files:**
- Create: `server/security/replay_cache.py`
- Create: `server/security/rate_limiter.py`
- Create: `server/security/audit.py`
- Modify: `server/session_manager.py`
- Modify: `server/message_handler.py`
- Modify: `server/websocket_server.py`
- Modify: `server/config.py`
- Modify: `web/app.py`
- Create: `tests/test_websocket_security.py`
- Modify: `tests/test_api_negative.py`

**Interfaces:**
- Produces: bounded TTL `ReplayCache.consume(key, expires_at) -> bool`.
- Produces token-bucket limits by IP, node, and global scope.
- Produces redacted `SecurityAuditEvent` records.

- [ ] **Step 1: Write failing replay, spoofing, size, and rate tests**

```python
def test_consumed_pairing_token_cannot_register_again():
    assert register_once(qr_token).accepted
    assert register_once(qr_token).error_code == "PAIRING_REPLAYED"

def test_node_rotation_cannot_bypass_ip_and_global_budget():
    limiter = RateLimiter(policy=TEST_POLICY, clock=clock)
    decisions = [limiter.allow(ip="10.0.0.2", node=f"n{i}", action="register") for i in range(20)]
    assert decisions.count(False) > 0

def test_audit_event_never_serializes_secret():
    assert qr_token not in json.dumps(audit.events)
```

- [ ] **Step 2: Run security tests and verify failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_websocket_security.py tests/test_api_negative.py -q`

- [ ] **Step 3: Implement bounded security services**

Evict expired replay keys, cap cache size, apply message byte limits before JSON/base64 decode, validate image dimensions before inference, and return structured retry durations. Production origin/TLS policy is explicit configuration; local development policy is visibly labelled.

- [ ] **Step 4: Run complete security and protocol regression**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_websocket_security.py tests/test_api_negative.py tests/test_system_contract.py tests/test_communication_server.py tests/test_webrtc_ingest.py -q`

- [ ] **Step 5: Run full phase verification and commit**

Run full backend, web build, mobile tests/type-check. Commit as `security: harden camera pairing and message ingress`.
