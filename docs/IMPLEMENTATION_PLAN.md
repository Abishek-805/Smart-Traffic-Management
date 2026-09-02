# App, backend and web repair plan

This plan reconciles the current source with the original problem reports in the
provided conversation export. Historical completion claims are not verification.

## Scope and order

1. Reproducible startup: isolated Python environment, explicit configuration,
   correct Docker contents, deterministic model paths, setup and launch commands.
2. Connections: valid URLs, directional pairing, issued session credentials,
   reconnect cleanup, REST commands and telemetry shared across services.
3. Mobile capture: stable native preview, bounded serial sampling, resource
   cleanup, stop/resume lifecycle, real native APK compatibility.
4. Perception: one inference per frame, independent ByteTrack state per camera,
   explicit one-camera/one-approach assignment and count/queue units, bounded stale state.
5. Signals: serialized decisions and time-driven phase updates, explicit yellow
   phase, stopped and unavailable-input states, truthful hardware status.
6. Observability: measured per-camera rates, frame age, latency and counters;
   no invented operational data or unlabelled demo feeds.
7. UI: four readable camera panels, top phase/countdown bar, automatic previews,
   real device actions, responsive layout, coherent theme and error states.
8. Validation: existing tests plus defect regressions, service integration,
   production web build, native checks, real YOLO inference, physical-phone tests.

## Acceptance

- A fresh checkout can install and start with documented commands.
- A phone's direction and session survive reconnect without another direction's
  stream or tracker being overwritten by stale connections.
- Slow processing cannot accumulate unbounded frame queues.
- Start/stop/disconnect affect the server, not only browser storage.
- Frames, counts and status flow through the deployed split-server topology.
- Signal timing does not freeze just because no new frames arrive.
- Missing data is shown as unavailable; demo, simulation and live operation are
  explicitly distinguished.
- UI and API agree on direction, duration, status and measurement units.
- No claim of flicker-free physical operation without observation on the device.
- One-, two-, then four-phone endurance tests and ESP32 prototype tests require
  those devices to be available; unperformed checks must stay documented.

## Capability limits

YOLO26n COCO weights currently recognize bicycle, car, motorcycle, bus and truck classes.
Emergency-vehicle recognition and reinforcement learning are not implemented
capabilities of this model. Do not advertise them as verified features.
Native preview FPS, transmitted samples per second, inference FPS and network
latency are separate measurements. JPEG sampling is not full-rate video.

Preserve the existing camera/pipeline/control/hardware separation and tests.
Mobile cameras are the intended operating source. Demo input is explicit only;
hardware is not activated without selecting the physical port.

## Implementation status (1 September 2026)

| Stage | Result |
| --- | --- |
| Startup | Combined runtime, isolated Python 3.12 environment and Windows launcher implemented; installed launch verified. Fresh-machine and Docker installs remain unverified. |
| Connections | Issued credentials, socket ownership, direction collisions, reconnect cleanup and real REST command acknowledgments implemented and regression-tested. |
| Mobile capture | Stable preview lifecycle, serial native resize/encode, processed-frame ACK backpressure, selectable 2/4 FPS profiles, resource disposal, cancellation and keep-awake implemented; TypeScript/Android JS export pass. Native build/device check remains open. |
| Perception | Shared detector with separate ByteTrack associations, global-ID reset fix, confirmed track history and correct metric units implemented. Accuracy calibration remains open. |
| Signals | Clockwise demand-aware phases, empty/stale skipping, bounded adaptive green, early empty-lane release, green/yellow/all-red timing and emergency precedence implemented and tested; stale/paused UI is all-red. Hardware remains simulation. |
| Observability | Actual per-direction freshness/rates/counters, processed-frame/server/queue/inference latency, retained Redis state, error acknowledgments, and removal of fabricated history/status implemented. |
| UI | Four feeds, top phase bar, always-visible main-dashboard directional QR pairing, larger metrics, honest unavailable states, responsive controls and light/dark theme implemented and browser-checked. |
| Validation | Four independent session tests, real-image pipeline smoke tests, production web build, Android type checking and prior four-client load measurements are available. Physical four-phone and trained-model accuracy gates remain. |

## Remaining release gates, in order

1. Install/configure JDK and Android SDK, compile the native Android app, then resolve
   any native build/runtime errors exposed by actual hardware.
2. Run one/two/four-phone tests for at least 15 minutes, including stop/start,
   disconnect/reconnect and background/foreground. Measure frame age, CPU, memory
   and visible preview stability instead of assuming the code fix proves them.
3. Download the official IISc UVH-26 release, prepare it with
   `scripts/prepare_uvh26.py`, fine-tune YOLO26n, and evaluate the untouched
   validation plus a labelled local-camera set. See `docs/MODEL_TRAINING.md`.
4. Resolve remaining Expo 54 dependency advisories through a native-tested upgrade.
5. Validate the Docker topology with real Redis, including service restarts and
   temporary loss of Redis; in-process fake-Redis contract tests are not that check.
6. Add authenticated operators and authenticated pairing plus TLS before any public
   hosting. Current QR/session handling is for a trusted LAN only.
7. Keep ESP32 disconnected from real traffic infrastructure until hardware behavior,
   safe fallback and relevant engineering requirements have been independently tested.

Emergency detection, RL optimization and historical efficiency analytics are separate
unimplemented capabilities, not repaired features or proven model outputs.
