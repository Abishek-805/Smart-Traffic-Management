# SIH Requirement Compliance & Traceability Matrix

**Project:** Smart Traffic Management System  
**Date:** 18 September 2026  
**Audited Repositories:**  
- `Smart-Traffic-Management` (`https://github.com/Abishek-805/Smart-Traffic-Management.git`)  
- `Traffic_Camera_App` (`https://github.com/Abishek-805/Traffic_Camera_App.git`)  
**Audit Standard:** Strict source-code evidence only. Classification labels: `VERIFIED`, `MEASURED`, `SIMULATED`, `PARTIAL`, `UNVERIFIED`, `NOT IMPLEMENTED`.

---

## 1. Traceability Matrix

| Requirement ID | Description | Source File / Implementation | Evidence & Test Suite | Status | Practical Limitation / Defense |
|---|---|---|---|---|---|
| **REQ-AI-01** | Multi-class vehicle detection | `ai/detection/detector.py`, `ai/models/model_manager.py` | PyTorch YOLOv8n (classes: car, bus, truck, motorcycle, bicycle); test `tests/test_batch_detection.py` | `VERIFIED` | Uses standard COCO-pretrained weights. Not retrained on local Indian junction dataset. |
| **REQ-AI-02** | Multi-camera object tracking | `ai/tracking/byte_tracker.py`, `ai/pipeline/traffic_pipeline.py` | 4 isolated `ByteTracker` instances (`self.trackers[lane]`); test `test_tracker_instances_do_not_rewind_existing_ids` | `VERIFIED` | ID persistence verified per lane; cross-lane re-identification not attempted (by design). |
| **REQ-AI-03** | Observation vs Prediction separation | `ai/state/vehicle_state_manager.py`, `ai/detection/detection_types.py` | `ObservationState.OBSERVED` vs `PREDICTED`; Kalman predictions excluded from vehicle counts; test `test_observation_semantics.py` | `VERIFIED` | Prevents ghost vehicles and phantom queues during detector skips. |
| **REQ-AI-04** | Emergency vehicle priority preemption | `ai/signal/signal_scheduler.py`, `ai/signal/priority_calculator.py` | Scheduler preemption logic implemented; tests `test_emergency_preempts_starvation_only_when_fresh`, `test_emergency_override.py` | `PARTIAL` | **Logic verified in simulation; Model weights DO NOT detect ambulances/fire trucks.** (COCO weights lack emergency class). |
| **REQ-ENG-01** | Passenger Car Equivalent (PCE) analytics | `ai/analytics/occupancy_analyzer.py`, `ai/analytics/analytics_exporter.py` | Weighted factors (car=1.0, bus/truck=2.5, motorcycle=0.5, bicycle=0.2); test `test_priority_calculator.py` | `VERIFIED` | Weights conform to Indian IRC:106 guidelines. |
| **REQ-ENG-02** | Real-time queue length & wait estimation | `ai/state/vehicle_state_manager.py`, `ai/analytics/congestion_analyzer.py` | Pixel velocity threshold (`QUEUE_MOTION_THRESHOLD_PX_SEC = 5.0`); consecutive frame accumulator; test `test_observation_semantics.py` | `VERIFIED` | Requires calibrated camera angle for physical metric distance conversion. |
| **REQ-SIG-01** | Dynamic adaptive green allocation | `ai/signal/signal_scheduler.py` | Absolute demand formula (`0.75 * load_ratio + 0.25 * queue_ratio`); bounded in $[5\text{s}, 120\text{s}]$; test `test_adaptive_green_uses_absolute_demand_and_stays_bounded` | `VERIFIED` | Single vehicle on empty junction receives minimum green (5s), not maximum. |
| **REQ-SIG-02** | Starvation prevention & round-robin fairness | `ai/signal/signal_scheduler.py` | Clockwise service order (`NORTH -> EAST -> SOUTH -> WEST`); skips empty/stale lanes; test `test_scheduler_serves_each_occupied_lane_once_in_clockwise_cycle` | `VERIFIED` | Formally prevents starvation; permanently busy approaches cannot lock green. |
| **REQ-SIG-03** | Yellow & All-Red transition intervals | `ai/signal/signal_controller.py`, `ai/signal/signal_scheduler.py` | Fixed 3.0s yellow phase; all-red clearance interval before switching green; test `test_signal_controller.py` | `VERIFIED` | Prevents intersection collisions during phase switches. |
| **REQ-NET-01** | Dynamic mobile camera pairing | `web/services/node_service.py`, `server/session_manager.py` | Single-use dynamic QR code generation with UUIDv4 pairing token & 5-min TTL; test `test_registration_requires_matching_one_time_qr_token` | `VERIFIED` | Eliminates manual IP entry on phone nodes. |
| **REQ-NET-02** | High-throughput video ingest | `server/webrtc_ingest.py`, `server/message_handler.py` | WebRTC sendonly track (8 FPS) via `aiortc`; JPEG/base64 fallback; test `test_webrtc_ingest.py` | `VERIFIED` | Tested with up to 4 concurrent synthetic video peers. |
| **REQ-NET-03** | Closed-loop backpressure & RTT tracking | `server/message_handler.py`, mobile `UploadWorker.ts` | Server returns `FRAME_ACK` with processing and queue metrics; client adjusts delay; test `test_e2e_pipeline_websocket.py` | `VERIFIED` | Client throttle prevents buffer bloat under network degradation. |
| **REQ-HW-01** | Microcontroller hardware actuation (ESP32) | `ai/hardware/esp32_interface.py`, `ai/hardware/command_encoder.py` | PySerial driver with non-blocking write & ACK read; test `test_esp32_hardware_mode_uses_configured_port_and_records_ack` | `SIMULATED` | Serial command protocol tested via mock serial; physical hardware unvalidated in software repo. |
| **REQ-HW-02** | Fail-closed all-red hardware safety | `server/runtime.py`, `ai/hardware/esp32_interface.py` | Halts automatic switching; enforces `ALL_RED` if configured ESP32 disconnects; test `test_requested_esp32_failure_forces_safe_all_red_and_visible_error` | `VERIFIED` | Never silently falls back to simulation mode when hardware requested. |
| **REQ-EDG-01** | Low-power edge deployment (Raspberry Pi) | `config/deployment.py`, `ai/models/model_manager.py` | Immutable profile defined; NCNN runtime configured; batch-1 strictly enforced; test `test_raspberry_pi_profile_is_proposed_and_batch_one` | `PROPOSED_UNVALIDATED` | Software configuration verified; physical Pi benchmarks not yet conducted. |
| **REQ-OPS-01** | Centralized web control center | `web-ui/src/App.tsx`, `web/routes/dashboard_routes.py` | Single-page React 19 application; real-time telemetry; multi-camera visualizer; build verified `570ms` | `VERIFIED` | Responsive dark UI with status indicators, configuration modal, and log viewer. |
| **REQ-MOB-01** | Dedicated mobile camera client | `traffic-camera-app` (React Native / Expo 54) | Camera2 / VisionCamera capture; QR scanner; WebRTC stream; native orientation correction; `npm test` passed | `VERIFIED` | Requires custom dev client build (Expo Go unsupported due to WebRTC/VisionCamera C++ JSI modules). |

---

## 2. Hardware vs. Software Scope Boundaries

To maintain scientific integrity during technical evaluations, the boundaries of software verification are explicitly defined:

```text
[SOFTWARE REPOSITORY SCOPE — VERIFIED]
- Algorithm correctness (Fairness, PCE, Kalman tracking, Queue estimation)
- Network protocol integrity (WebRTC, WebSocket, Pydantic, JSON/hex encoding)
- Fault isolation, backpressure, and fail-closed safety transitions
- End-to-end multi-camera synchronization and web UI dashboard

[PHYSICAL HARDWARE BOUNDARY — UNVALIDATED / SIMULATED]
- Physical Raspberry Pi 4/5 thermal throttling and FPS on ARM Linux
- Physical ESP32 PCB soldering, GPIO relay logic, and optical signal heads
- Actual Indian junction camera placement, lens distortion, and night lighting
- Dedicated emergency vehicle siren acoustic detection or custom visual dataset
```
