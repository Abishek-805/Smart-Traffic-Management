# SIH Requirement Compliance & Traceability Matrix

**Project:** Smart Traffic Management System  
**Date:** 18 September 2026  
**Audited Repositories:**  
- `Smart-Traffic-Management` (`https://github.com/Abishek-805/Smart-Traffic-Management.git`)  
- `Traffic_Camera_App` (`https://github.com/Abishek-805/Traffic_Camera_App.git`)  
**Overall Verdict:** Core software-testable requirements verified; hardware/data-dependent requirements remain partial or unvalidated.

---

## 1. Traceability Matrix

| Requirement ID | Description | Source File / Implementation | Evidence & Test Suite | Status | Practical Limitation / Defense |
|---|---|---|---|---|---|
| **REQ-AI-01** | Multi-class vehicle detection | `ai/detection/detector.py`, `ai/models/model_manager.py` | PyTorch YOLOv8n (classes: car, bus, truck, motorcycle, bicycle); test `tests/test_batch_detection.py` | `VERIFIED` | Uses standard COCO-pretrained weights. **Formal detection accuracy is not yet quantitatively validated** (no labelled dataset in repo). |
| **REQ-AI-02** | Multi-camera object tracking | `ai/tracking/byte_tracker.py`, `ai/pipeline/traffic_pipeline.py` | 4 isolated `ByteTracker` instances (`self.trackers[lane]`); test `test_tracker_instances_do_not_rewind_existing_ids` | `VERIFIED` | ID persistence verified per lane; cross-lane re-identification not attempted (by design). |
| **REQ-AI-03** | Observation vs Prediction separation | `ai/state/vehicle_state_manager.py`, `ai/detection/detection_types.py` | `ObservationState.OBSERVED` vs `PREDICTED`; Kalman predictions excluded from vehicle counts; test `test_observation_semantics.py` | `VERIFIED` | Prevents ghost vehicles and phantom queues during detector skips. |
| **REQ-AI-04** | Emergency vehicle priority preemption | `ai/signal/signal_scheduler.py`, `ai/signal/priority_calculator.py` | Scheduler preemption logic implemented; tests `test_emergency_preempts_starvation_only_when_fresh`, `test_emergency_override.py` | `PARTIAL` | **Logic verified in simulation; Model weights DO NOT detect ambulances/fire trucks.** (COCO weights lack emergency vehicle classes). |
| **REQ-ENG-01** | Passenger Car Equivalent (PCE) analytics | `ai/analytics/occupancy_analyzer.py`, `ai/analytics/analytics_exporter.py` | Configured weights: Car=1.0, Bus=1.5, Truck=2.0, Motorcycle=0.5, Bicycle=0.5, 3-wheeler=0.8; test `test_priority_calculator.py` | `VERIFIED` | Configured in `config/traffic.py` per traffic flow standards. |
| **REQ-ENG-02** | Real-time queue length & wait estimation | `ai/state/vehicle_state_manager.py`, `ai/analytics/congestion_analyzer.py` | Pixel velocity threshold (`QUEUE_MOTION_THRESHOLD_PX_SEC = 15.0 px/s`); 10 consecutive frames; test `test_observation_semantics.py` | `VERIFIED` | Requires calibrated camera geometry for metric distance conversion. |
| **REQ-SIG-01** | Dynamic adaptive green allocation | `ai/signal/signal_scheduler.py` | Absolute demand formula (`0.75 * load_ratio + 0.25 * queue_ratio`); default min 10s, max 60s (API configurable 5s to 120s); test `test_adaptive_green_uses_absolute_demand_and_stays_bounded` | `VERIFIED` | Light demand receives minimum green (10s), not maximum. |
| **REQ-SIG-02** | Starvation prevention & round-robin fairness | `ai/signal/signal_scheduler.py` | Clockwise service order (`NORTH -> EAST -> SOUTH -> WEST`); skips empty/stale lanes; test `test_scheduler_serves_each_occupied_lane_once_in_clockwise_cycle` | `VERIFIED` | Prevents starvation; permanently busy approaches cannot hold green. |
| **REQ-SIG-03** | Yellow & All-Red transition intervals | `ai/signal/signal_controller.py`, `ai/signal/signal_scheduler.py` | Fixed 3.0s yellow (`YELLOW_SEC = 3`); 2.0s all-red clearance (`ALL_RED_SEC = 2`); test `test_signal_controller.py` | `VERIFIED` | Prevents intersection collisions during phase switches. |
| **REQ-NET-01** | Dynamic mobile camera pairing | `web/services/node_service.py`, `server/session_manager.py` | Single-use dynamic QR code generation with UUIDv4 pairing token & 5-min TTL; test `test_registration_requires_matching_one_time_qr_token` | `VERIFIED` | Eliminates manual IP entry on phone nodes. |
| **REQ-NET-02** | High-throughput video ingest | `server/webrtc_ingest.py`, `server/message_handler.py` | WebRTC sendonly track (8 FPS cap) via `aiortc`; JPEG/base64 fallback; test `test_webrtc_ingest.py` | `VERIFIED` | Tested with up to 4 concurrent synthetic video peers. |
| **REQ-NET-03** | Closed-loop backpressure & RTT tracking | `server/message_handler.py`, mobile `UploadWorker.ts` | Server returns `FRAME_ACK` with processing and queue metrics; client adjusts delay; test `test_e2e_pipeline_websocket.py` | `VERIFIED` | Client throttle prevents buffer bloat under network degradation. |
| **REQ-HW-01** | Microcontroller hardware actuation (ESP32) | `ai/hardware/esp32_interface.py`, `ai/hardware/command_encoder.py` | PySerial driver with non-blocking write & ACK read; test `test_esp32_hardware_mode_uses_configured_port_and_records_ack` | `SIMULATED` | Serial command protocol verified via mock serial; physical hardware unvalidated in software repo. |
| **REQ-HW-02** | Fail-closed all-red hardware safety | `server/runtime.py`, `ai/hardware/esp32_interface.py` | Halts automatic switching; enforces `ALL_RED` if configured ESP32 disconnects; test `test_requested_esp32_failure_forces_safe_all_red_and_visible_error` | `VERIFIED` (Software logic) | Software fail-closed logic verified; physical hardware safety unvalidated. |
| **REQ-EDG-01** | Low-power edge deployment (Raspberry Pi 5) | `config/deployment.py`, `ai/models/model_manager.py` | Immutable profile defined; NCNN runtime configured; batch-1 strictly enforced; input size 512; test `test_raspberry_pi_profile_is_proposed_and_batch_one` | `PROPOSED_UNVALIDATED` | Software configuration verified; physical Raspberry Pi 5 benchmarks not yet conducted. |
| **REQ-OPS-01** | Centralized web control center | `web-ui/src/App.tsx`, `web/routes/dashboard_routes.py` | Single-page React 19 application; real-time telemetry; multi-camera visualizer; build verified `570ms` | `VERIFIED` | Responsive dark UI with status indicators, configuration modal, and log viewer. |
| **REQ-MOB-01** | Dedicated mobile camera client | `traffic-camera-app` (React Native / Expo 54) | Camera2 / VisionCamera capture; QR scanner; WebRTC stream; native orientation correction; `npm test` passed | `VERIFIED` | Requires custom dev client build (Expo Go unsupported due to WebRTC/VisionCamera C++ JSI modules). |

---

## 2. Hardware vs. Software Scope Boundaries

To maintain scientific integrity during technical evaluations, the boundaries of software verification are explicitly defined:

```text
[SOFTWARE REPOSITORY SCOPE — VERIFIED]
- Algorithm correctness (Clockwise round-robin fairness, PCE, Kalman tracking, Queue estimation)
- Network protocol integrity (WebRTC, WebSocket, Pydantic, JSON/hex encoding)
- Fault containment, backpressure, and fail-closed safety transitions in software
- End-to-end multi-camera synchronization and web UI dashboard

[PHYSICAL HARDWARE BOUNDARY — UNVALIDATED / SIMULATED]
- Physical Raspberry Pi 5 thermal throttling, CPU temperatures, and sustained FPS on ARM Linux
- Physical ESP32 PCB wiring, GPIO relay logic, and 12V/240V optical signal heads
- Actual Indian junction camera placement, lens distortion, rain, and night lighting
- Dedicated emergency vehicle visual detection (requires custom fine-tuning) or siren acoustic classifier
- Quantitative precision/recall/mAP (requires annotated ground-truth traffic dataset)
```
