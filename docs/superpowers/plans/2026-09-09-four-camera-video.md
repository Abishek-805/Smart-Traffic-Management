# Four camera video implementation plan

**Goal:** QR-paired concurrent phone video, shared low-latency inference and independent lane tracking, with local camera compatibility.
**Spec:** ../specs/2026-09-09-four-camera-streaming-inference-design.md

- [ ] Add and test ordered batch detection with independent downstream trackers; measure CPU batching before selecting defaults.
- [ ] Replace per-lane executor backlog with one coordinator that takes the newest direction slots when the worker is available. Authenticate again before and after work.
- [ ] Add WebRTC ingest with four owned peers, bounded negotiation, continuously drained decode and sampled decoded-frame submission. Test real local peer connections, expiry and replacement.
- [ ] Add negotiated mobile video with camera lifecycle cleanup and visible JPEG fallback. Preserve QR ownership and heartbeats. Typecheck and run mobile protocol regressions.
- [ ] Add direct USB/file/RTSP/Picamera2 source bridge feeding the same frame submission API.
- [ ] Compare four-source runtime against saved serial baseline; test timing rules, stop/start, replacement, stale input and reconnection. Record measured limits and device-only checks.

Ruling: existing user changes stay in place on codex/four-lane-video. Work occurs in the shared checkout because the requested baseline includes uncommitted changes. No push or APK publication.
Ruling: a batched model API is available, but batch size is selected from measurements; batch4 is not assumed faster on a CPU.
