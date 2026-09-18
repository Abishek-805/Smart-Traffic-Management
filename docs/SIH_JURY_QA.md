# SIH Technical Defense & Jury Question-and-Answer (Q&A)

**Project:** Smart Traffic Management System  
**Date:** 18 September 2026  
**Audited Repositories:**  
- `Smart-Traffic-Management` (`https://github.com/Abishek-805/Smart-Traffic-Management.git`)  
- `Traffic_Camera_App` (`https://github.com/Abishek-805/Traffic_Camera_App.git`)  
**Purpose:** Technical jury defense guide for Smart India Hackathon (SIH) evaluators, technical reviewers, and academic judges. All numeric values match the current source code exactly.

---

## Category 1: AI, Computer Vision & Tracking

### Q1: "You claim to use YOLOv8n. Is this trained on Indian traffic datasets (e.g., IDD), or are you using generic COCO weights?"
**Answer:**
> "We use standard YOLOv8n weights (`yolov8n.pt`, 6.5 MB) pre-trained on COCO-80, filtered strictly at inference to 5 vehicle classes: `bicycle` (1), `car` (2), `motorcycle` (3), `bus` (5), and `truck` (7).
> 
> We explicitly state: **Formal detection accuracy is not yet quantitatively validated** because no labelled traffic dataset is currently checked into the repository. We do not make unsubstantiated mAP, precision, or recall claims. Our contribution is the end-to-end perception, tracking, and closed-loop scheduling pipeline. Fine-tuning on Indian datasets (such as IDD or IISc UVH-26) is the immediate next step in our roadmap."

### Q2: "How does your system handle emergency vehicles (ambulances, fire engines)? Can it distinguish an ambulance from a commercial white delivery van?"
**Answer:**
> "In the current codebase, emergency vehicle detection is **partially implemented**:
> 1. The **scheduling pre-emption logic** is fully implemented and mathematically verified: when an approach flags emergency demand, the scheduler pre-empts normal round-robin cycles to grant immediate green clearance (`test_emergency_preempts_starvation_only_when_fresh`).
> 2. However, standard COCO weights do **not** contain an `ambulance` or `fire_truck` class. In production, `is_priority` defaults to `False`. Standard YOLOv8n classifies an ambulance as a `car` or `bus`. Real-world visual emergency distinction requires fine-tuning on a labelled emergency dataset or deploying an acoustic siren detection model on the edge node."

### Q3: "What exact thresholds govern your ByteTrack tracker? How does it handle occlusions?"
**Answer:**
> "Our tracking layer in `ai/tracking/byte_tracker.py` configures the following exact parameters from `config/model.py`:
> - `TRACK_HIGH_THRESHOLD = 0.15`: First association pass matches high-confidence detections to existing tracks.
> - `TRACK_LOW_THRESHOLD = 0.08`: Second association pass matches weak detections ($0.08 \le \text{conf} < 0.15$) against unmatched tracks, recovering occluded vehicles.
> - `NEW_TRACK_THRESHOLD = 0.15`: Weak boxes below 0.15 can **never** initiate a new track.
> - `TRACK_MATCH_THRESHOLD = 0.80`: Spatial matching cost threshold.
> - `TRACK_BUFFER_FRAMES = 12`: Number of frames a lost track is retained during total occlusion.
> - `MIN_CONFIRMATION_FRAMES = 2`: Consecutive observed frames required before a track enters confirmed vehicle counts.
> - `TRACK_REMOVAL_GRACE_SEC = 1.8s` and `TRACK_EXPIRATION_TIMEOUT_SEC = 4.0s`: Inactivity timeouts for cleaning up stale tracks.
> 
> Crucially, intermediate Kalman projections (`ObservationState.PREDICTED`) are **display-only** and strictly barred from updating counts or queues."

### Q4: "Why don't you use cross-camera vehicle re-identification (Re-ID)?"
**Answer:**
> "Each camera monitors an incoming approach to a single four-way junction. Vehicles enter from the perimeter and clear through the intersection. Tracking a vehicle across approaches is unnecessary for localized junction control and would introduce prohibitive computational overhead ($O(N^2)$ feature embedding comparisons). Isolating independent `ByteTracker` instances per approach completely eliminates global ID collisions and guarantees deterministic $O(1)$ tracking per lane."

---

## Category 2: Traffic Engineering & Signal Scheduling

### Q5: "How do you prevent starvation? If North has 50 vehicles and East has only 1, won't North keep the green light forever?"
**Answer:**
> "No. Starvation is **mathematically impossible** in our scheduling algorithm. In `ai/signal/signal_scheduler.py`, we enforce a **clockwise round-robin cycle** (`NORTH -> EAST -> SOUTH -> WEST`):
> 1. Traffic demand dictates the **duration** of the green phase (bounded between `min_green_sec = 10s` and `max_green_sec = 60s` by default, tunable via REST API within $[5\text{s}, 120\text{s}]$), **not** the turn order.
> 2. Even if North has overwhelming demand, once its green timer reaches `max_green_sec`, the cursor advances clockwise to the next occupied approach.
> 3. Approaches with zero demand or disconnected cameras are skipped in $O(1)$ time without wasting minimum green time. Lane East is guaranteed service within at most one full cycle."

### Q6: "If North has only 1 light scooter and all other lanes are empty, will it receive the maximum 60 seconds of green?"
**Answer:**
> "No. We calculate green duration using **absolute approach demand**, rather than a relative ratio against other lanes:
> $$\text{ratio} = 0.75 \times \min\left(1.0, \frac{\text{PCE}}{\text{FULL\_GREEN\_PCE}}\right) + 0.25 \times \min\left(1.0, \frac{\text{QueueSec}}{\text{FULL\_GREEN\_QUEUE\_SEC}}\right)$$
> where `FULL_GREEN_PCE = 20.0` and `FULL_GREEN_QUEUE_SEC = 120.0s`.
> 
> In `config/traffic.py`, a motorcycle has a PCE weight of $0.5$. The resulting demand ratio is $< 0.02$, which evaluates to the minimum bound of $\mathbf{10\text{ seconds}}$ (or 5s if configured). The system never allocates maximum green to negligible traffic."

### Q7: "What are your exact transition intervals between phases?"
**Answer:**
> "The signal controller enforces two mandatory safety intervals configured in `config/signal.py`:
> 1. A fixed **3.0-second Yellow phase** (`YELLOW_SEC = 3`) on the terminating approach to permit vehicles in the dilemma zone to clear safely.
> 2. A fixed **2.0-second All-Red clearance interval** (`ALL_RED_SEC = 2`) where all 4 approaches display red simultaneously before the green phase activates on the winning approach. This guarantees mutual exclusion and physical junction clearance."

### Q8: "What are your exact PCE weights and queue detection thresholds?"
**Answer:**
> "From `config/traffic.py`:
> - **PCE Weights:** `car`: 1.0, `bus`: 1.5, `truck`: 2.0, `motorcycle`: 0.5, `bicycle`: 0.5, `three-wheeler`: 0.8, `two-wheeler`: 0.5, `van`/`suv`: 1.2.
> - **Queue Motion Threshold:** `QUEUE_MOTION_THRESHOLD_PX_SEC = 15.0 px/s`.
> - **Consecutive Queue Frames:** `CONSECUTIVE_QUEUE_FRAMES = 10`. A vehicle must remain below 15 px/s for 10 consecutive frames before being marked queued.
> - **Count Stabilization:** Exponential Moving Average smoothing with `EMA_ALPHA = 0.4` over a 10-frame window (`COUNT_HISTORY_SIZE = 10`)."

---

## Category 3: Edge Computing, Hardware & Embedded Actuation

### Q9: "Can a Raspberry Pi actually run this system in real time with 4 camera feeds? What is your target board?"
**Answer:**
> "Our designated edge target is the **Raspberry Pi 5** (64-bit Raspberry Pi OS, Quad-core Cortex-A76, active cooling).
> 
> On a Pi 5 running stock PyTorch with batch-4, real-time operation is unfeasible. We architected an explicit `RASPBERRY_PI` profile in `config/deployment.py`:
> - Switches runtime to **NCNN** with ARM NEON SIMD optimizations.
> - Enforces **batch size = 1** (sequential single-frame processing).
> - Drops input resolution to $512 \times 512$ (`YOLO_INPUT_SIZE = 512`).
> - Configures camera capture to 2.0 FPS (`capture_fps = 2.0`) and detector cadence to 1.0 FPS (`detector_fps = 1.0`), bridging intermediate frames with Kalman prediction.
> 
> However, to maintain scientific honesty: in our audit, the Raspberry Pi profile is classified as **`PROPOSED_UNVALIDATED`**. While configuration and batch-1 constraints are fully verified in regression tests (`test_deployment_profile.py`), we have not yet benchmarked thermal throttling on physical Raspberry Pi 5 silicon."

### Q10: "How does the physical traffic light interface with your software? What if the serial cable is disconnected?"
**Answer:**
> "The software interfaces with an ESP32 microcontroller via PySerial at 115200 baud (`ESP32_BAUDRATE = 115200`), transmitting ASCII command packets (`PHASE:NORTH:GREEN:30\n`) and reading ACK responses.
> 
> If the serial cable is disconnected or communication fails:
> 1. PySerial raises an I/O exception which is caught and recorded in `HardwareStatus`.
> 2. The hardware connection state transitions to `HardwareConnectionState.ERROR`.
> 3. The runtime **fails closed in software**: it halts automated phase cycling and commands an `ALL_RED` state.
> 4. It never silently pretends to be in simulation mode when hardware was explicitly requested. Physical hardware safety itself remains unvalidated."

---

## Category 4: Networking, Ports & Mobile Node

### Q11: "Which ports are used? Does the camera connect to 8000 or 8001?"
**Answer:**
> "This depends strictly on the deployment mode:
> - **Combined Mode (`run.py` / `web/app.py`):** Single-process deployment. Port **8000** serves REST API (`/api/v1`), Static Web UI, Camera WebSocket (`/ws/camera`), and Telemetry WebSocket (`/ws/telemetry`).
> - **Split Microservice Mode (`docker-compose.yml`):**
>   - Port **8000**: `app-backend` (REST API).
>   - Port **8001**: `websocket-server` (Camera WebSocket `/ws/camera`).
>   - Port **6379**: Redis Pub/Sub.
>   - Port **5173**: Vite development server.
> 
> When an operator generates a pairing QR code, the backend automatically embeds the correct active port (`CAMERA_WS_PORT`), so the mobile app always connects to the right port without manual configuration."

### Q12: "Can your mobile app run in Expo Go?"
**Answer:**
> "No. Expo Go is strictly unsupported. Our mobile app utilizes `react-native-webrtc` and `react-native-vision-camera`, both of which require custom native C++ code and Android Camera2 JSI bindings. The app is compiled as an Expo custom development client (`npx expo run:android` / EAS Build)."

### Q13: "What is your measured system latency?"
**Answer:**
> "We do not claim a blanket 'latency guarantee.' On a standard laptop CPU host with 4 camera feeds:
> - **Server pipeline latency:** Measured at p50 of 310.9 ms and p95 of 371.6 ms across 4 simultaneous streams.
> - **End-to-end transport ACK latency:** Measured at p50 of 324 ms and p95 of 527 ms under localhost WebSocket load.
> - **Coordinator queue wait time:** Typically 20–85 ms (p50), rising to ~260 ms under peak batch alignment.
> - **Frame age at decision:** Ranging between 350 ms and 650 ms."

---

## Category 5: Security & Practical Limitations

### Q14: "Is your system secure? Can someone inject fake frames to force a green light?"
**Answer:**
> "Our current security model is designed for a local demonstration network:
> 1. **Dynamic Pairing:** Pairing requires scanning a dynamic QR code containing a UUIDv4 token with a 5-minute TTL. Upon registration, the token is destroyed immediately.
> 2. **Socket Pinning:** The server pins the session token to the specific TCP connection handle, rejecting frame injection from other sockets.
> 
> **Explicit Limitations:**
> - Operator REST endpoints (`/api/v1/system/start`, `/stop`, `/config`) are **currently unauthenticated** on the local LAN.
> - Traffic is cleartext HTTP/WS by default.
> - Municipal road deployment will require JWT/RBAC authorization, TLS (HTTPS/WSS), and physical tamper-proofing. The current prototype is not certified for public roads."
