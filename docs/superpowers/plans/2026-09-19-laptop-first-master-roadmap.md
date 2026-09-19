# Laptop-First Portable Validation Master Roadmap

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a laptop-validated, measurable traffic-management software stack while keeping Raspberry Pi and physical signal behavior behind unvalidated deployment adapters.

**Architecture:** Preserve Mobile Camera -> WebRTC/JPEG -> Backend -> YOLOv8n -> ByteTrack -> Traffic Analytics -> Signal Scheduler -> Dashboard. Execute four independently reviewable plans in dependency order; each extends existing components and produces working software before the next begins.

**Tech Stack:** Python 3, FastAPI, asyncio, aiortc, Ultralytics YOLOv8n/PyTorch, ByteTrack, OpenCV, pytest, React/Vite/TypeScript, Expo/React Native/WebRTC.

**Spec:** `docs/superpowers/specs/2026-09-19-laptop-first-portable-validation-design.md`

## Global Constraints

- Laptop is the authoritative software acceptance environment.
- Preserve protocol version `1.0`, QR pairing, WebRTC, JPEG fallback, YOLOv8n, ByteTrack, PCE, queue handling, scheduler safety, operator authentication, and the React/Vite dashboard.
- Do not import Raspberry-Pi-only or GPIO packages in the base laptop environment.
- Do not claim Raspberry Pi, ESP32, physical signal, accelerator, or emergency-vehicle recognition validation without physical evidence.
- Do not change model identity, thresholds, or input resolution merely to increase FPS.
- Keep one replaceable pending frame per direction and preserve confirmed traffic state when frames become stale.
- Run focused tests, the full backend suite, cross-repository checks, mobile tests/type-check, and the web build after every significant phase.
- Preserve the untracked user files `Review 1_ppt[1].pptx` and `Smart_Traffic_Management_Review_Presentation.pptx`.

## Review Focus

- A delayed disconnect from an old socket must not remove a newer session for the same node; pinned by generation tests in Plan 1 Task 1.
- Client capture timestamps may be missing, non-finite, or from a skewed clock; pinned by timing tests in Plan 1 Task 4.
- A high-rate camera must not starve quiet cameras during continuous replacement; pinned by fairness tests in Plan 1 Task 3.
- An evaluation report must not merge external and project-owned datasets into an unexplained metric; pinned by provenance tests in Plan 2 Task 1.
- Unsupported Pi metrics and hardware adapters must report `unsupported`/`unavailable`, never simulated success; pinned by capability tests in Plan 4 Tasks 1-2.

---

## Audit Baseline

- Backend repository: `C:\Users\ashek\Desktop\smart-traffic-management`
- Branch: `codex/four-lane-video`
- Audited HEAD: `248349732d5cf0d09ebbf9e965f15a07a998961e`
- Mobile repository: `C:\Users\ashek\Desktop\traffic-camera-app`, branch `main`, HEAD `463ffee4fc5caa9a48c240aaaec09079d11dce1f`
- Mobile implementation branch: fast-forward existing `codex/stream-startup-fps` from `main` before its first change (`main` is one commit ahead and the branch has no unique commits at audit time).
- Backend tests: `153 passed, 1 warning in 44.57s` using `.venv\Scripts\python.exe -m pytest -q`
- Web UI: `npm run build` passed.
- Mobile: `npm test` and `npm run type-check` passed.
- Startup: `start.ps1 -Lan`, or `scripts/run.ps1 -Lan` after `scripts/setup.ps1`; direct combined runtime is `python run.py --host 0.0.0.0 --port 8000`.
- Model/runtime: `yolov8n.pt`, PyTorch, input 576, confidence 0.08, IoU 0.60, four CPU threads.
- Laptop deployment defaults: WebRTC sampling 4 FPS, detector 2 FPS/direction, batch 4, preview 4 FPS.
- Warm-up: synchronous inside `ModelManager._load_model()` using the configured batch, without explicit load/first/second/steady timing or staged readiness.
- Camera lifecycle today: pairing/session/connection/frame freshness are stored separately; dashboard derives mostly `OFFLINE/CONNECTING/LIVE/STALE` and a registered session can be counted as connected before usable media.
- Frame coordinator today: latest-frame dictionary by direction, 20 ms collection delay, stale rejection at 2.5 seconds, one executor, configured batches, no explicit round-robin cursor.
- Scheduler today: freshness filtering, fairness/cycle behavior, bounded diagnostics, emergency flag handling, minimum/maximum green and safety tests already exist.
- Existing assets to extend: model evaluator, traffic replay lab, homography calibration, digital intersection, operator authentication, deployment profiles, WebRTC/JPEG ingest, and benchmark scripts.

## Plan Sequence

1. `docs/superpowers/plans/2026-09-19-connection-performance-observability.md`
   - Session generations, lifecycle truth, takeover, bounded fair slots, stage timing, WebRTC stats, staged readiness, batching benchmark, adaptive cadence decision.
2. `docs/superpowers/plans/2026-09-19-model-quality-perception.md`
   - Evaluation manifest/schema, scene and size breakdowns, reproducible gates, tracking/count stability, calibrated queue semantics, experimental flags.
3. `docs/superpowers/plans/2026-09-19-scheduler-testlab-security.md`
   - Simulated emergency event contract, decision records/dashboard, deterministic replay, impairment/load/soak harness, security hardening.
4. `docs/superpowers/plans/2026-09-19-deployment-final-validation.md`
   - Portable adapters/profiles, system metrics providers, optional runtime qualification, complete acceptance suite and final evidence report.

Each plan must be merged into the same `codex/four-lane-video` branch in order. A later plan may consume only interfaces explicitly produced by an earlier plan.

## Specification Coverage

| Master-prompt phases | Owning plan/tasks |
|---|---|
| Connection, lifecycle, reconnect, takeover | Plan 1 Tasks 1-2 |
| Latest-frame slots, stale rejection, fairness | Plan 1 Task 3 |
| Full latency and WebRTC observability | Plan 1 Tasks 4-5 |
| Warm-up/readiness, batching, 1-4 camera evidence | Plan 1 Tasks 6-7 |
| Optional adaptive cadence | Plan 1 Task 8 |
| Evaluation manifest and model reports | Plan 2 Tasks 1-3 |
| Tracking/count and calibrated queue semantics | Plan 2 Task 4 |
| Additional perception feature gates | Plan 2 Task 5 |
| Simulated emergency lifecycle | Plan 3 Task 1 |
| Scheduler explainability | Plan 3 Task 2 |
| Deterministic replay | Plan 3 Task 3 |
| Network/multi-camera simulation, resource limits, soak | Plan 3 Task 4 |
| Pairing, replay, validation, rate limits, audit security | Plan 3 Task 5 |
| Deployment profiles and lazy platform adapters | Plan 4 Task 1 |
| Laptop/Pi/fake metrics providers | Plan 4 Task 2 |
| ONNX/NCNN/accelerator qualification | Plan 4 Task 3 |
| Documentation, final acceptance, evidence report | Plan 4 Task 4 |

## Mobile Branch Preflight

- [ ] **Step 1: Fast-forward the existing mobile Codex branch without rewriting history**

```powershell
Push-Location ..\traffic-camera-app
git switch codex/stream-startup-fps
git merge --ff-only main
git status --short --branch
Pop-Location
```

Expected: `codex/stream-startup-fps` points at the current mobile baseline and retains no unrelated working-tree changes.

## Program Completion Gate

- [ ] **Step 1: Run the complete laptop acceptance command set**

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Push-Location web-ui; npm run build; Pop-Location
Push-Location ..\traffic-camera-app; npm test; npm run type-check; Pop-Location
```

Expected: backend suite, UI build, mobile regressions, and mobile TypeScript all pass.

- [ ] **Step 2: Verify evidence inventory**

Run:

```powershell
.\.venv\Scripts\python.exe scripts\validate_evidence.py --report LAPTOP_FIRST_VALIDATION_REPORT.md
```

Expected: exit 0; every PASS statement references a machine-readable artifact containing commit, configuration, model hash, environment, trial count, and source parameters.

- [ ] **Step 3: Verify prohibited claims are absent**

Run:

```powershell
rg -n "Pi.*validated|ESP32.*validated|real emergency vehicle detection" LAPTOP_FIRST_VALIDATION_REPORT.md docs
```

Expected: no unsupported physical-validation claim; any matching text is explicitly negated or labelled future work.

- [ ] **Step 4: Commit the final evidence index**

```powershell
git add LAPTOP_FIRST_VALIDATION_REPORT.md docs scripts/validate_evidence.py
git commit -m "docs: publish laptop-first validation evidence"
```
