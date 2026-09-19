# Deployment Abstraction and Final Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete portable deployment/configuration boundaries, expose truthful platform metrics, qualify optional runtimes only through evidence, and publish the final laptop-first validation report.

**Architecture:** Formalize the existing deployment profiles around lazy capability adapters for frame sources, inference, metrics, and signal output. Keep Windows fully operational when Pi packages are absent, provide fake providers for deterministic tests, and make the final report mechanically traceable to machine-readable evidence.

**Tech Stack:** Python/dataclasses/ABC/psutil/subprocess/pytest, JSON evidence, PowerShell, existing React/FastAPI status APIs.

**Spec:** `docs/superpowers/specs/2026-09-19-laptop-first-portable-validation-design.md`

## Global Constraints

- Profiles are `laptop`, `raspberry-pi-5`, and `accelerated` with aliases handled explicitly for current `raspberry_pi` compatibility.
- Pi/GPIO/camera packages are never imported at module import time on Windows.
- Unsupported hardware reports `unsupported`/`unavailable`, never connected or validated.
- ONNX/NCNN/accelerator runtimes remain candidates until all gates pass.
- Final PASS claims require referenced evidence; missing, failed, manual-not-run, and future-hardware items remain visible.

## Review Focus

- Importing all deployment modules on Windows must succeed without Picamera2/GPIO; Task 1 pins this.
- Malformed `vcgencmd` output must produce unsupported/error fields rather than zero temperature; Task 2 pins this.
- Environment/effective configuration output must redact secrets and tokens; Task 1 pins this.
- A runtime candidate with incomplete evidence must be rejected even if its FPS is higher; Task 3 pins this.
- The final report validator must reject PASS rows whose artifacts are missing or refer to another commit; Task 4 pins this.

---

### Task 1: Portable Adapter Registry and Three Deployment Profiles

**Files:**
- Create: `platform_adapters/capabilities.py`
- Create: `platform_adapters/frame_sources.py`
- Create: `platform_adapters/inference.py`
- Create: `platform_adapters/signal_output.py`
- Modify: `config/deployment.py`
- Modify: `server/local_sources.py`
- Modify: `server/runtime.py`
- Modify: `ai/hardware/esp32_interface.py`
- Create: `tests/test_platform_adapters.py`
- Modify: `tests/test_deployment_profile.py`

**Interfaces:**
- Produces: `CapabilityStatus(name, status: "available" | "unavailable" | "unsupported", detail)`.
- Produces lazy registries `create_frame_source(profile)`, `create_inference_runtime(profile)`, `create_signal_output(profile)`.
- Produces `DeploymentProfile.to_public_dict()` with secrets redacted.

- [ ] **Step 1: Write failing Windows import/capability/profile tests**

```python
def test_pi_profile_loads_without_pi_packages_on_windows(monkeypatch):
    block_imports(monkeypatch, ["picamera2", "RPi.GPIO"])
    profile = load_deployment_profile({"TRAFFIC_PROFILE": "raspberry-pi-5"})
    assert profile.validation_status == "PROFILE_PREPARED_NOT_HARDWARE_VALIDATED"
    assert capability_registry.probe("picamera2").status == "unavailable"

def test_effective_config_redacts_secrets():
    public = profile_with(pairing_secret="secret-value").to_public_dict()
    assert "secret-value" not in json.dumps(public)
```

- [ ] **Step 2: Run test and verify current two-profile contract fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_platform_adapters.py tests/test_deployment_profile.py -q`

- [ ] **Step 3: Implement lazy import factories and compatible profile aliases**

```python
ADAPTER_FACTORIES = {
    "webrtc": lambda: WebRTCFrameSource,
    "jpeg": lambda: JPEGFrameSource,
    "picamera2": lambda: importlib.import_module("platform_adapters.pi_camera").PiCameraSource,
}
```

Only invoke Pi imports when that adapter is selected and capability probing succeeds. Keep `raspberry_pi` as a deprecated alias for `raspberry-pi-5` so existing environment files continue to work.

- [ ] **Step 4: Run deployment, hardware, startup, and runtime tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_platform_adapters.py tests/test_deployment_profile.py tests/test_control_logging_hardware.py tests/test_startup.py tests/test_runtime_regressions.py -q`

- [ ] **Step 5: Commit**

Commit as `refactor: isolate platform deployment adapters`.

### Task 2: System Metrics Providers and Resource Warning Policy

**Files:**
- Create: `platform_adapters/system_metrics.py`
- Modify: `core/application_context.py`
- Modify: `web/schemas.py`
- Modify: `web/routes/api_routes.py`
- Create: `tests/test_system_metrics.py`
- Modify: `tests/test_operational_logging.py`

**Interfaces:**
- Produces: `SystemMetricsProvider.sample() -> SystemMetrics`.
- Produces `LaptopMetricsProvider`, lazy `RaspberryPiMetricsProvider`, and `FakeMetricsProvider`.

- [ ] **Step 1: Write failing unsupported, parse, and warning tests**

```python
def test_laptop_reports_pi_fields_as_unsupported():
    sample = LaptopMetricsProvider().sample()
    assert sample.temperature_c.status == "unsupported"
    assert sample.throttled.status == "unsupported"

def test_bad_vcgencmd_output_is_not_reported_as_zero():
    sample = RaspberryPiMetricsProvider(run=lambda *_: "garbage").sample()
    assert sample.temperature_c.value is None
    assert sample.temperature_c.status == "error"

def test_fake_throttle_causes_degraded_resource_health():
    health = resource_health(FakeMetricsProvider(throttled=True).sample())
    assert health.status == "DEGRADED"
```

- [ ] **Step 2: Run test and verify provider seam is absent**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_system_metrics.py tests/test_operational_logging.py -q`

- [ ] **Step 3: Implement providers with status-bearing values**

```python
@dataclass(frozen=True)
class MetricValue:
    value: float | int | bool | None
    status: Literal["available", "unsupported", "unavailable", "error"]
    unit: str | None = None
```

Parse `get_throttled` bit flags into current and historical undervoltage, capped, throttled, and soft-temperature-limit fields. Never run `vcgencmd` on unsupported hosts.

- [ ] **Step 4: Run focused and API tests**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_system_metrics.py tests/test_operational_logging.py tests/test_web_application.py -q`

- [ ] **Step 5: Commit**

Commit as `feat: expose truthful portable system metrics`.

### Task 3: Optional Runtime Qualification Matrix

**Files:**
- Create: `ai/evaluation/runtime_qualification.py`
- Modify: `scripts/export_edge_model.py`
- Modify: `scripts/benchmark_edge_models.py`
- Create: `scripts/qualify_runtime.py`
- Create: `tests/test_runtime_qualification.py`
- Modify: `docs/MODEL_EVALUATION.md`
- Modify: `docs/RASPBERRY_PI_DEPLOYMENT.md`

**Interfaces:**
- Consumes evaluation/gate reports from Plan 2 and performance/soak evidence from Plans 1/3.
- Produces `RuntimeQualification(status="accepted"|"rejected"|"incomplete", failures, evidence)`.

- [ ] **Step 1: Write failing completeness and accuracy-first tests**

```python
def test_fast_candidate_with_missing_soak_is_incomplete():
    result = qualify(candidate_evidence(with_soak=False))
    assert result.status == "incomplete"

def test_fast_candidate_with_accuracy_failure_is_rejected():
    result = qualify(candidate_evidence(map_gate=False, all_other_gates=True))
    assert result.status == "rejected"
```

- [ ] **Step 2: Run test and verify qualification API is absent**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_runtime_qualification.py -q`

- [ ] **Step 3: Implement eight required gates**

Require accuracy evaluation, cold startup, warm startup, one-camera, two-camera, four-camera, soak, and complete regression evidence. Runtime exports are stored as candidates and never update the production profile automatically.

- [ ] **Step 4: Qualify current PyTorch baseline and inventory candidates**

```powershell
.\.venv\Scripts\python.exe scripts/qualify_runtime.py --runtime pytorch --evidence docs/benchmarks --output docs/benchmarks/runtime-pytorch-qualification.json
.\.venv\Scripts\python.exe scripts/qualify_runtime.py --runtime onnx --evidence docs/benchmarks --output docs/benchmarks/runtime-onnx-qualification.json
```

Expected: PyTorch reflects available evidence; candidates with absent gates are `incomplete`, not accepted.

- [ ] **Step 5: Run tests and commit**

Commit as `test: gate optional inference runtimes on complete evidence`.

### Task 4: Evidence Validator, Final Acceptance, and Report

**Files:**
- Create: `scripts/validate_evidence.py`
- Create: `tests/test_evidence_validator.py`
- Create: `LAPTOP_FIRST_VALIDATION_REPORT.md`
- Modify: `README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/TEST_STRATEGY.md`
- Modify: `docs/RASPBERRY_PI_DEPLOYMENT.md`
- Modify: `docs/SECURITY_AUDIT.md`

**Interfaces:**
- Produces validator exit 0 only when every PASS report entry has an existing compatible artifact for the current commit/configuration.

- [ ] **Step 1: Write failing missing-artifact and wrong-commit tests**

```python
def test_pass_without_artifact_is_rejected(tmp_path):
    report = write_report(tmp_path, status="PASS", evidence="missing.json")
    assert validate_report(report).errors == ["missing evidence: missing.json"]

def test_artifact_from_other_commit_is_rejected(tmp_path):
    artifact = write_artifact(tmp_path, git_commit="deadbeef")
    assert "commit mismatch" in validate_artifact(artifact, current_commit="abc123").errors
```

- [ ] **Step 2: Run tests and verify validator is absent**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_evidence_validator.py -q`

- [ ] **Step 3: Implement report/evidence validation and write report sections**

The report contains all 22 required sections and a table for automated laptop, manual laptop, mobile-device, simulated hardware, future Pi, and future ESP32 evidence. Status values are `PASS`, `FAIL`, `NOT_RUN`, `SIMULATED`, and `FUTURE_HARDWARE`; only PASS requires successful measured evidence.

- [ ] **Step 4: Run final acceptance suite**

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Push-Location web-ui; npm run build; Pop-Location
Push-Location ..\traffic-camera-app; npm test; npm run type-check; Pop-Location
.\.venv\Scripts\python.exe scripts/run_replay.py --scenarios tests/fixtures/replay/golden-scenarios.json --seed 42 --output docs/benchmarks/final-replay.json
.\.venv\Scripts\python.exe scripts/run_multicamera_lab.py --cameras 1,2,3,4 --duration 30 --output docs/benchmarks/final-multicamera.json
.\.venv\Scripts\python.exe scripts/run_soak.py --duration 90 --output docs/benchmarks/final-short-soak.json
.\.venv\Scripts\python.exe scripts/validate_evidence.py --report LAPTOP_FIRST_VALIDATION_REPORT.md
```

Expected: all automated gates pass. Manual/mobile physical trials not run in this execution remain `NOT_RUN`, and physical Pi/ESP32 remain `FUTURE_HARDWARE`.

- [ ] **Step 5: Check claims and repository cleanliness**

```powershell
git diff --check
git status --short
rg -n "Pi.*validated|ESP32.*validated|real emergency vehicle detection" LAPTOP_FIRST_VALIDATION_REPORT.md docs
```

Expected: only accurate negated/future-hardware language; user PowerPoint files remain untracked and untouched.

- [ ] **Step 6: Commit final documentation and evidence index**

```powershell
git add scripts/validate_evidence.py tests/test_evidence_validator.py LAPTOP_FIRST_VALIDATION_REPORT.md README.md docs
git commit -m "docs: publish laptop-first validation report"
```
