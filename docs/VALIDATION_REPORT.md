# Repair validation report — 1 September 2026

## Outcome

Software repairs are implemented in both repositories. Local automated checks and
browser checks pass. This is not a claim that every original complaint has been
verified on physical phones or that the prototype is production-ready.

The supplied ChatGPT export was treated as historical context. Source code,
dependency APIs and executed checks took precedence over earlier completion claims.

## Main defects addressed

| Observed defect | Repair |
| --- | --- |
| Split REST and camera services had disconnected state and simulated success | Shared runtime contract, retained Redis snapshots/frames, expiring state, command acknowledgments and reconnect loops |
| QR navigation discarded direction/TLS/expiry; later frames used the wrong credential | Preserve the full QR payload, send explicit direction even with opaque session IDs, persist ACK token, authenticate later frames/heartbeats and verify socket ownership |
| Stream buttons and device disconnect could update only local UI state | Server-acknowledged actions and real socket/session removal |
| Camera preview was forcibly remounted; capture work could overlap | Stable preview mount, serial async snapshot/resize/encode, processed-frame ACK backpressure, generation cancellation and native object disposal |
| Model/tracker state could mix cameras; creating a tracker could rewind global IDs | One detector inference per frame, independent per-direction ByteTrack association and protected ID allocation |
| Quadrant assignment omitted vehicles from approach cameras | Explicit one-camera/one-approach counting, without misleading four-quadrant overlays |
| A stalled direction affected perceived health of all feeds | Independent direction age and status, latest-frame buffering, bounded send times |
| Signal timing depended on arrival of another frame | Independent runtime tick; stopped/unavailable inputs show all-red |
| Counts, wait, priority, latency and analytics had inconsistent or invented meanings | Scheduler-derived priority, stopped-vehicle queue units, measured frame/server/queue/inference timings, confirmed-track history; unavailable historical/device data remains unavailable |
| QR direction/address and desktop/mobile layouts were confusing | Explicit direction selector, real QR generation errors/expiry, top phase bar, four panels, responsive controls and light/dark theme |
| Setup depended on hidden files, demo inputs and incompatible Python installation | Isolated Python 3.12 environment, model path fallback, corrected Docker contents, combined launcher and rewritten setup docs |

## Executed checks

| Check | Result and limits |
| --- | --- |
| Python suite | **56 passed**. Includes one-time QR authorization, reconnect-window preservation, combined-runtime QR defaults, fresh-input eligibility, starvation/emergency precedence, bounded diagnostics and real local YOLO inference; it is not an accuracy benchmark. |
| Detector A/B | **YOLO26n selected**. In a same-machine four-client comparison, both models acknowledged 324/324 frames. YOLO26n reduced mean inference p95 (62.84 vs 65.20 ms), CPU p50 (140.6 vs 147.65% of one core), and RSS p50 (308.69 vs 394.78 MB); ACK and preview p95 remained within about 6 ms and 3 ms. |
| QR/mobile registration flow | **Passed live**: dashboard/API generated `10.1.111.101:8000`; incorrect secrets were rejected; the valid client registered, stopped/resumed, received processed-frame ACKs, reconnected with its issued token and disconnected cleanly. Warm local frame RTT averaged 35.5 ms in the focused protocol check. |
| Four-client runtime load | **Passed again with secured pairing** against combined FastAPI on port 8000: 324/324 frames acknowledged over 20 seconds at 4.05 FPS per direction. Direction ACK p95 was 133.8–138.7 ms, inference p95 34.9–36.2 ms, preview-arrival p95 188.9–215.4 ms, RSS p50 388.5 MB with 0.23 MB growth. The longer pre-security run also acknowledged 960/960 over 60 seconds. Local clips/localhost, not four real phones. |
| Redis contract | **Passed with fakeredis**: late REST consumer receives retained state and JPEG, command round trip returns an acknowledgment. Missing Redis does not report success. |
| Runtime settings | **Passed**: confidence/min/max applied, invalid values rejected. Browser Save returned runtime acknowledgment. |
| Web production build | **Passed**, TypeScript + Vite 8.2.2. Final JS approximately 314 kB, 93 kB gzip. |
| Browser checks | Dashboard, devices, direction QR generation and runtime Save exercised. 390×844 and desktop viewport checked; no horizontal overflow on dashboard/devices after fixes. Light/dark theme tested and restored to dark. |
| Mobile TypeScript | **Passed**. |
| Mobile protocol regressions | **Passed**: ACK credentials, server-controlled streaming, authenticated frame fields, matching processed-frame backpressure/latency, heartbeat RTT units, disconnect identity, expired QR rejection, explicit East direction and TLS with an opaque session ID. Native APIs are mocked. |
| Expo dependency alignment | **Passed**, SDK 54 expected dependencies. |
| Android JavaScript/Hermes export | **Passed**, 1,204 modules and approximately 3.22 MB bundle. This is not an APK or native camera test. |
| EAS Android APK | **Passed**: corrected preview build `84a59562-fb48-4e59-a4c0-edcd9de91fdf`, Expo SDK 54, app `1.0.1` (build 2), signed with the project's remote Android credentials. The 125,332,209-byte APK was downloaded and SHA-256 verified. Physical QR-to-stream retest remains required. |
| Tooling UUID compatibility | **Passed** for CommonJS consumers after uuid override; xcode UUID generation and ngrok module load checked without starting a tunnel. |
| Windows launcher | **Passed installed-environment launch** with SkipInstall; loaded YOLO and served UI/REST/WebSocket. Full first-run steps were executed separately; fresh-machine install was not tested. |
| Web npm audit | **0 reported vulnerabilities** after compatible web tooling updates. |
| Mobile npm audit | **8 high and 6 moderate advisories remain**, propagated through the Expo/Metro image-size and React Navigation/query-string dependency chains. The registry proposes major platform changes rather than a compatible patch. PostCSS and uuid findings are addressed with pinned overrides. No critical advisories reported. |

## What remains unverified or unimplemented

1. **Physical camera behavior.** The EAS Android APK builds and is signed, but preview
   flicker, permission handling, camera switching, thermal/memory behavior and device
   resume still require observation on the target phones.
2. **Endurance and latency.** Run one, two and four phones for 15+ minutes. The
   selectable 2/4 Hz target and bounded queues do not prove a specific phone-to-dashboard delay.
   Measure with a visible clock; backend inference duration is not network RTT.
3. **Model accuracy.** The existing COCO weights recognize car/motorcycle/bus/truck.
   No labelled project dataset or quantitative acceptance target was supplied.
   Use `scripts/evaluate_detector.py --data <traffic.yaml>` when labels are available.
   Counts, stopped-vehicle estimates and tracking need camera/site calibration,
   especially for occlusion, night footage and moving phones.
4. **Dependencies.** The remaining image-size advisories have no patched version
   in its current npm release line observed during this run. Review upstream patches
   or an Expo/Metro migration; verify native compatibility before adopting the
   major upgrade proposed by npm audit.
5. **Docker and real Redis recovery.** Docker was unavailable. Container definitions
   were repaired and Redis semantics tested in-process; production container startup,
   network interruptions and Redis restarts have not been executed.
6. **Security.** Trusted LAN only. Initial camera registration now requires the
   direction-bound, expiring, one-time QR secret and reconnect uses an issued session
   token. REST operator controls still lack authentication. Add operator authorization,
   TLS and request limits before public hosting. Android LAN cleartext is intentional
   in this prototype.
7. **ESP32 and public-road safety.** Web runtimes remain in simulation. Hardware
   fail-safe behavior, serial command delivery and regulatory/engineering acceptance
   have not been validated. Do not attach to public-road signals.
8. **Capabilities not supplied by the model.** Emergency-vehicle recognition,
   reinforcement learning, persisted hourly/daily analytics and efficiency improvement
   baselines are not implemented or advertised as working.

## Run and review

- Backend/web: follow root README.md, using start.ps1 -Lan.
- Mobile: follow ../traffic-camera-app/README.md for native Android build prerequisites.
- Implementation order and release gates: IMPLEMENTATION_PLAN.md.
- No commits, pushes or public deployment were performed. One internally distributed
  EAS preview APK was built for physical-device testing.
- The pre-existing deletion of the mobile .freebuff/project-id file was preserved.

## Primary references used

- [Ultralytics tracking](https://docs.ultralytics.com/modes/track/): tracking lifecycle;
  installed BYTETracker and BaseTrack source also inspected for version-specific APIs.
- [Vite 8 migration](https://v8.vite.dev/guide/migration): frontend build migration;
  Node requirements checked against npm package metadata.
- [Expo custom native code](https://docs.expo.dev/workflow/customizing/): why native
  modules require an app build rather than Expo Go.
- [Expo local native builds](https://docs.expo.dev/guides/local-app-overview/):
  Android build workflow.
- [React Native environment setup](https://reactnative.dev/docs/next/set-up-your-environment):
  Java/Android toolchain prerequisites.
- [Expo 54 keep-awake](https://docs.expo.dev/versions/v54.0.0/sdk/keep-awake/):
  screen-awake lifecycle.
- Installed VisionCamera 5.2.2 and Nitro Image source/types: snapshot and async
  image resize/encoding/disposal APIs.
- npm registry/audit: exact dependency versions and reported advisories, including
  [image-size ICNS](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr) and
  [image-size JXL/HEIF](https://github.com/advisories/GHSA-5p2g-fcmc-qvqq).
