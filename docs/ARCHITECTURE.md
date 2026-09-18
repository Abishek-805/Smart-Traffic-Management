# Smart Traffic Management System — Software Architecture (v2.0)

## 1. Executive Architecture Summary

The Smart Traffic Management System is a distributed, real-time edge platform that continuously ingests video from four approaches (North, East, South, West), estimates vehicular demand using computer vision and kinematics, and dynamically calculates optimal traffic light timings to minimize congestion and prevent intersection starvation.

The system is deployed across two decoupled repositories:
1. **Repository A (Mobile Camera Node — `traffic-camera-app`)**: Mobile edge client running on commodity Android/iOS devices providing video capture, hardware rotation compensation, and low-latency WebSocket/WebRTC streaming.
2. **Repository B (Smart Traffic Management Backend — `smart-traffic-management`)**: Core perception, tracking, analytics, scheduling, SCADA web dashboard, and hardware actuation engine.

---

## 2. End-to-End System Topology

```
   APPROACH 1 (North)     APPROACH 2 (East)      APPROACH 3 (South)     APPROACH 4 (West)
  [ Mobile Camera Node ] [ Mobile Camera Node ] [ Mobile Camera Node ] [ Mobile Camera Node ]
            │                      │                      │                      │
   Dynamic QR Pairing     Dynamic QR Pairing     Dynamic QR Pairing     Dynamic QR Pairing
   HMAC-SHA256 Token      HMAC-SHA256 Token      HMAC-SHA256 Token      HMAC-SHA256 Token
            │                      │                      │                      │
            └──────────────────────┼──────────────────────┴──────────────────────┘
                                   ▼
                   Local Wi-Fi Network (LAN / Private Subnet)
                                   │
                                   ▼
             FastAPI Control Center & Ingestion Server (Port 8000)
       ┌─────────────────────────────────────────────────────────────────┐
       │ WebSocket Endpoint: /ws/camera (Token pinned to socket session) │
       │ REST Endpoint: /api/v1/* (Optional OPERATOR_API_KEY security)   │
       │ Static UI Mount: / (React/Vite Production Dashboard)            │
       └─────────────────────────────────┬───────────────────────────────┘
                                         ▼
                     Multi-Camera Batch Frame Coordinator
                     (Bounded Single-Worker Executor Queue)
                         - Stale Frame Drop (> 2500 ms)
                         - Dynamic Resolution Scaling
                         - Batch Synchronization Barrier
                                         │
                                         ▼
                        AI Vehicle Perception Engine
                 ┌───────────────────────────────────────────────┐
                 │ Model: YOLOv8n (PyTorch FP32, 6.5 MB)         │
                 │ Classes: Car, Bus, Truck, Motorcycle, Bicycle │
                 │ Warmup: 3 Batched Passes at Startup           │
                 │ Input Resolution: 576px (Laptop) / 512px (Pi) │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                      Multi-Approach Kinematic Tracking
                 ┌───────────────────────────────────────────────┐
                 │ 4 Independent ByteTracker Instances           │
                 │ Low Confidence Recovery (conf >= 0.08)        │
                 │ Min Confirmation Frames: 2                    │
                 │ Track Removal Grace: 1.8s, Timeout: 4.0s      │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                       Vehicle State & Observation Logic
                 ┌───────────────────────────────────────────────┐
                 │ OBSERVED vs PREDICTED Separation              │
                 │ Motion Threshold: 15.0 px/s (10 frames)       │
                 │ Metric Queue Homography ([u, v] -> [X, Y] m)  │
                 │ Exponential Moving Average (EMA) Smoothing    │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                        Traffic Analytics & Priority Engine
                 ┌───────────────────────────────────────────────┐
                 │ Passenger Car Equivalent (PCE) Aggregation    │
                 │ Congestion Scoring (PCE: 0.45, Queue: 0.35)   │
                 │ Emergency Vehicle Override Detection          │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                        Adaptive Signal Decision Engine
                 ┌───────────────────────────────────────────────┐
                 │ Clockwise Round-Robin (Anti-Starvation)       │
                 │ Demand Ratio Green Time (10s <= tg <= 60s)    │
                 │ Mandatory Yellow (>= 3s) & All-Red (>= 2s)    │
                 │ Mutual Exclusion Safety Invariant Enforced    │
                 └───────────────────────┬───────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     Hardware Actuation Layer                        Real-Time Telemetry & SCADA
   ┌───────────────────────────┐                   ┌─────────────────────────────┐
   │ Hardware Mode: Simulation │                   │ Telemetry WS: /ws/telemetry │
   │ Mode ESP32: Serial 115200 │                   │ React Vite Web UI (Port 8000)│
   │ Fail-Closed Safe Cycle    │                   │ MJPEG Video Streams         │
   └───────────────────────────┘                   └─────────────────────────────┘
```

---

## 3. Core Architectural Subsystems

### A. Mobile Camera Node (`traffic-camera-app`)
- **Camera Lifecycle**: Implemented using React Native VisionCamera with orientation listeners ensuring vertical/horizontal upright normalization before JPEG compression.
- **Backpressure Regulation**: Single-flight WebSocket architecture (`max_pending_frames=1`). The mobile node does not emit frame $N+1$ until receiving `FRAME_ACK` for frame $N$.
- **Dual Pipeline**: Primary low-overhead JPEG-over-WebSocket lane capped at 8.0 FPS; optional WebRTC streaming lane for high-bandwidth previews.

### B. Frame Coordinator & Concurrency Model (`server/frame_coordinator.py`)
- Ingested frames from the 4 approaches are placed into an atomic dictionary (`handler.latest_frames`).
- A single background worker dequeues up to 4 frames simultaneously into a batch tensor.
- Synchronous PyTorch inference and tracking run within a bounded `ThreadPoolExecutor(max_workers=1)`.
- If a frame's latency exceeds $2500\text{ ms}$, it is dropped immediately to prevent stale decision actuation.

### C. Kinematic Tracking & Observation Semantics (`ai/tracking/`, `ai/state/`)
- To prevent track ID collisions across independent cameras, each approach maintains an isolated `ByteTracker` instance.
- **Observation Separation**: Detections produced by the YOLO detector are marked `ObservationState.OBSERVED`. Interpolated Kalman predictions are marked `ObservationState.PREDICTED`.
- **Prediction Immunity**: `PREDICTED` tracks are strictly restricted to UI rendering continuity. They are mathematically blocked from incrementing vehicle counts, queue counts, or PCE density.

### D. Ground-Plane Metric Queue Calibration (`ai/analytics/calibration.py`)
- Real-world road perspective is modeled via a 4-point homography matrix ($H$):
  $$\begin{bmatrix} X \\ Y \\ 1 \end{bmatrix} \sim H \begin{bmatrix} u \\ v \\ 1 \end{bmatrix}$$
- Transforms pixel centroids into meters from the stop line, enabling physical queue length estimation (meters) alongside vehicle counts.

### E. Signal Decision Engine (`ai/signal/`)
- **Clockwise Fair Scheduling**: The scheduler services occupied approaches in a deterministic sequence (`North \to East \to South \to West`).
- **Dynamic Green Duration**: Green time is calculated proportionally from approach demand:
  $$t_{\text{green}} = \text{MIN\_GREEN} + \text{ratio} \cdot (\text{MAX\_GREEN} - \text{MIN\_GREEN})$$
  Clamped strictly within $[10\text{s}, 60\text{s}]$.
- **Clearance Invariants**: Yellow interval ($\ge 3\text{s}$) and All-Red clearance ($\ge 2\text{s}$) are enforced before green switches.

### F. Security & Authentication Architecture (`server/session_manager.py`, `web/routes/api_routes.py`)
- **Camera Pairing**: Mobile nodes pair via dynamic QR codes with short-lived HMAC-SHA256 tokens pinned to unique node IDs.
- **Session Pinning**: Ingested frames are rejected if the session token does not match the active socket ownership.
- **Configurable Operator Authentication**:
  - Controlled by environment variables: `OPERATOR_AUTH_MODE=required|optional` (default: `optional`) and `OPERATOR_API_KEY`.
  - When `OPERATOR_AUTH_MODE=required`: All sensitive control endpoints (`/system/start`, `/system/stop`, `/system/restart`, `/system/override`, `/system/emergency-clear`, `/config/thresholds`, `/logs/export`, `DELETE /cameras/{direction}`) require `X-Operator-Token` validated using constant-time `hmac.compare_digest`.
  - Missing or empty `OPERATOR_API_KEY` in required mode causes startup validation failure (`RuntimeError`), preventing insecure boot.
  - In `optional` mode, a visible security notice is logged once to alert administrators, allowing trusted local LAN operation.
  - Public/read-only endpoints (`/system/health`, `/system/status`, `/system/digital-intersection`, `/cameras`, `/telemetry`) remain accessible without tokens for dashboard viewing.

### G. Cross-Repository Protocol Contract Testing (`tests/test_system_contract.py`)
- Programmatically inspects the sibling mobile repository (`traffic-camera-app`) on the local filesystem.
- Validates bidirectional contract invariants without adding mobile code as a runtime Python package:
  - **Protocol Version**: Asserts both repositories declare identical protocol version (`"1.0"`).
  - **Approach Directions**: Asserts identical four-way canonical sets (`{"north", "east", "south", "west"}`).
  - **Message Types**: Validates full 17-type message coverage between TypeScript constants and Python handlers.
  - **QR Code Payload**: Validates schema roundtrip compatibility for dynamic pairing.
  - **Port Topology**: Verifies network ports 8000 (combined) and 8001 (split WebSocket) align across mobile and backend configurations.

### H. Golden-Model Regression Testing (`tests/test_model_regression.py`)
- Employs an immutable, committed reference test asset (`tests/assets/model_regression/traffic_reference.jpg`) ensuring offline execution anywhere.
- Enforces structural invariants on the active YOLOv8n detector:
  - Valid detection counts ($\ge 1$, $\le 20$).
  - Classes belong strictly to traffic domain target classes (`bus`, `car`, etc.).
  - Coordinates reside strictly within frame bounds ($0 \le x_1 < x_2 \le W$, $0 \le y_1 < y_2 \le H$).
  - Confidence scores strictly bounded in $[0.0, 1.0]$.
  - Reasonable CPU inference latency.
- Numerical stability invariants:
  - Repeated inferences on the same static image yield identical detection counts and class labels.
  - Coordinate drift is bounded within $\le 3\text{ px}$ tolerance without fragile bit-exact floating point equality across different BLAS backends.

### I. Digital Intersection State View & Simulation Engine (`ai/pipeline/digital_intersection.py`)
- Provides a unified real-time 4-approach junction model (`North`, `East`, `South`, `West`).
- Exposes complete intersection snapshot via `GET /api/v1/system/digital-intersection`:
  - Active signal phase (`north_green`, `north_yellow`, `all_red`, etc.).
  - Per-approach traffic statistics (vehicles, queues, PCE, priority, camera health).
  - Countdown timer for active phase clearance.
  - Safety status (`NORMAL`, `DEGRADED`, `ALL_RED_HOLD`).
  - Cycle count tracker.
- Enforces critical safety invariants:
  - **Mutual Exclusion**: Never two conflicting greens simultaneously.
  - **Yellow Clearance**: Always precedes red transition ($\ge 3\text{s}$).
  - **All-Red Interval**: Clearance buffer ($\ge 2\text{s}$) between phase switches.
  - **Fail-Safe Fallbacks**: Active camera dropout initiates yellow clearance to safe red; AI stall immediately triggers `ALL_RED_HOLD`.

