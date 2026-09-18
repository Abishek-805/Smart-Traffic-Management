# SIH Technical Defense & Jury Question-and-Answer (Q&A)

**Project:** Smart Traffic Management System  
**Date:** 18 September 2026  
**Audited Repositories:**  
- `Smart-Traffic-Management` (`https://github.com/Abishek-805/Smart-Traffic-Management.git`)  
- `Traffic_Camera_App` (`https://github.com/Abishek-805/Traffic_Camera_App.git`)  
**Purpose:** Technical jury defense guide for Smart India Hackathon (SIH) evaluators, technical reviewers, and academic judges.

---

## Category 1: AI, Computer Vision & Tracking

### Q1: "You claim to use YOLOv8n. Is this trained on Indian traffic datasets (e.g., IDD), or are you using generic COCO weights?"
**Answer:**
> "We use standard YOLOv8n weights pre-trained on COCO-80, filtered strictly at inference to 5 vehicle classes: `car`, `bus`, `truck`, `motorcycle`, and `bicycle`. We have **not** yet fine-tuned on the India Driving Dataset (IDD) or local junction data. We openly document this in `docs/MODEL_AUDIT.md`. Our immediate contribution is the end-to-end perception, tracking, and closed-loop scheduling pipeline. Training on a dedicated Indian traffic dataset is the next milestone in our roadmap."

### Q2: "How does your system handle emergency vehicles (ambulances, fire engines)? Can it distinguish an ambulance from a commercial white delivery van?"
**Answer:**
> "In the current software codebase, emergency vehicle detection is **partially implemented**:
> 1. The **scheduling pre-emption engine** is fully implemented and mathematically verified: when an emergency vehicle is flagged on an approach, the scheduler immediately pre-empts normal round-robin cycles to grant immediate green clearance (`test_emergency_preempts_starvation_only_when_fresh`).
> 2. However, because standard COCO weights lack an `ambulance` or `emergency_vehicle` class, the current visual model cannot reliably distinguish an ambulance from a van. In production, `is_priority` defaults to `False`. We refuse to fabricate visual accuracy claims; real-world deployment requires either fine-tuning on emergency vehicle imagery or integrating an acoustic siren detection model on the edge node."

### Q3: "What happens when vehicles occlude each other in heavy bumper-to-bumper traffic?"
**Answer:**
> "We implement **ByteTrack** with four independent tracking instances (one per camera approach). ByteTrack differs from simple SORT by utilizing a two-stage association strategy:
> - High-confidence detections ($>0.5$) are matched first using Kalman filter projections and Hungarian linear assignment.
> - Low-confidence detections ($0.1 \le \text{conf} < 0.5$) are matched against unmatched tracks in a second pass, recovering occluded vehicles as they emerge.
> - Furthermore, between detector cycles (which run at 3 FPS), Kalman filters project vehicle trajectories. Crucially, as enforced by our P0-2 correctness fix, these projected boxes (`ObservationState.PREDICTED`) are **display-only** and strictly barred from inflating vehicle counts or triggering signal changes until confirmed by real detector evidence."

### Q4: "Why don't you use cross-camera vehicle re-identification (Re-ID)?"
**Answer:**
> "Each camera in our architecture monitors an incoming approach to a single four-way junction. Vehicles enter from the outside and exit away from the cameras. Tracking a vehicle across approaches is unnecessary for local signal control and would introduce high computational overhead ($O(N^2)$ feature embedding comparison). Isolating `ByteTracker` per approach completely eliminates global ID collision and guarantees deterministic $O(1)$ tracking per lane."

---

## Category 2: Traffic Engineering & Signal Scheduling

### Q5: "How do you prevent starvation? If North has 50 vehicles and East has only 1, won't North keep the green light forever?"
**Answer:**
> "No. Starvation is **mathematically impossible** in our scheduling algorithm. We enforce a **clockwise round-robin cycle** (`NORTH -> EAST -> SOUTH -> WEST`):
> 1. Traffic demand dictates the **duration** of the green phase (clamped between `min_green_sec=5s` and `max_green_sec=60s`), **not** who gets the next turn.
> 2. Even if North has overwhelming demand, once its green timer reaches `max_green_sec`, the cursor advances to the next occupied approach in clockwise order.
> 3. Approaches with zero demand or disconnected cameras are skipped in $O(1)$ time without wasting minimum green time. Therefore, Lane East is guaranteed service within at most one full cycle."

### Q6: "If North has only 1 light scooter and all other lanes are empty, will it receive the maximum 60 seconds of green?"
**Answer:**
> "No. We calculate green duration using **absolute approach demand**, rather than a relative ratio against other lanes:
> $$\text{ratio} = 0.75 \times \min\left(1.0, \frac{\text{PCE}}{\text{FULL\_GREEN\_PCE}}\right) + 0.25 \times \min\left(1.0, \frac{\text{QueueSec}}{\text{FULL\_GREEN\_QUEUE\_SEC}}\right)$$
> A single scooter has a PCE of only $0.5$ (per Indian IRC:106 standards). The resulting ratio is $<0.05$, which evaluates to the minimum bound of $\mathbf{5\text{ seconds}}$. The system never wastes green time on negligible traffic."

### Q7: "What happens during phase transitions? How do you prevent intersection collisions?"
**Answer:**
> "The signal controller enforces two mandatory safety clearance phases:
> 1. A fixed **3.0-second Yellow phase** on the terminating lane to allow clearing vehicles to exit the junction safely.
> 2. A configurable **All-Red clearance interval** where all 4 approaches display red simultaneously before the next approach receives the green signal. This guarantees mutual exclusion and physical safety."

---

## Category 3: Edge Computing, Hardware & Embedded Actuation

### Q8: "Can a Raspberry Pi 4 actually run this system in real time with 4 camera feeds?"
**Answer:**
> "On a Raspberry Pi 4 running stock PyTorch with a batch-4 tensor, real-time performance is not achievable. That is why we architected an explicit `RASPBERRY_PI` deployment profile (`config/deployment.py`):
> - Switches runtime from PyTorch to **NCNN** with ARM NEON SIMD vectorization.
> - Enforces **batch size = 1** (processing frames sequentially across cameras).
> - Drops input resolution from $576 \times 576$ to $320 \times 320$.
> - Reduces detector cadence to 2 FPS, bridging frames with Kalman projection.
> 
> However, to maintain scientific honesty: in our audit, the Raspberry Pi profile is classified as **`PROPOSED_UNVALIDATED`** because while the software configuration and batch-1 constraints are fully verified in regression tests (`test_deployment_profile.py`), we have not yet benchmarked thermal throttling on physical Raspberry Pi 4 silicon."

### Q9: "How does the physical traffic light interface with your software? What if the serial cable is disconnected?"
**Answer:**
> "The software interfaces with an ESP32 microcontroller via PySerial at 115200 baud, transmitting deterministic ASCII commands (e.g. `PHASE:NORTH:GREEN:30\n`) and reading ACK responses.
> 
> If the serial cable is disconnected or communication fails:
> 1. PySerial raises an I/O exception which is caught and logged.
> 2. The hardware state immediately transitions to `HardwareConnectionState.ERROR`.
> 3. The runtime **fails closed**: it halts automatic cycling and forces an `ALL_RED` state on the intersection.
> 4. The system **never** silently falls back to simulation mode when hardware was explicitly requested."

---

## Category 4: Mobile Node, Networking & WebRTC

### Q10: "Can your mobile app run in Expo Go?"
**Answer:**
> "No. Expo Go is strictly unsupported. Our mobile app utilizes `react-native-webrtc` and `react-native-vision-camera`, both of which require custom native C++ code and Android Camera2 JSI bindings. The app is compiled as a custom development client (`npx expo run:android` / EAS Build). Attempting to run it in standard Expo Go will fail immediately due to missing native modules."

### Q11: "Why do you support both WebRTC and WebSocket JPEG streaming?"
**Answer:**
> "We employ a **dual-transport strategy**:
> 1. **WebRTC (Primary):** Provides hardware-accelerated H.264 video encoding directly from the Android camera surface at 8 FPS, transmitting over UDP RTP with sub-50ms glass-to-glass latency and minimal battery consumption.
> 2. **WebSocket JPEG (Fallback):** In real-world field environments, municipal Wi-Fi networks or cellular carrier NATs frequently block UDP traffic or symmetric NAT traversal. If WebRTC ICE negotiation fails, the app automatically falls back to serialized JPEG snapshot streaming over standard TCP WebSocket."

### Q12: "How do you handle clock synchronization between 4 phones and the laptop? What if a phone's clock is 5 minutes fast?"
**Answer:**
> "We **do not trust client clocks**. All scheduling decisions, detector cadence intervals, and staleness evaluations rely solely on the server's monotonic clock (`time.monotonic()`), recorded as `backend_receive_monotonic` upon packet arrival. Phone timestamps are strictly echoed back in `FRAME_ACK` so the mobile node can compute its own round-trip time (RTT) using its internal clock."

---

## Category 5: Security & Field Reliability

### Q13: "What prevents someone on the same Wi-Fi network from hijacking the camera stream or sending fake traffic data?"
**Answer:**
> "Pairing is secured through a **zero-trust handshake**:
> 1. The operator generates a direction-specific QR code on the dashboard. This QR code embeds a cryptographically random UUIDv4 pairing token with a strict 5-minute time-to-live (TTL).
> 2. The phone scans the QR code and presents the token over WebSocket. Once verified, the pairing token is **immediately destroyed** (single-use).
> 3. The server issues a new session UUID and **pins that session to the physical TCP socket handle**. An attacker cannot inject frames using a stolen token from another connection, nor can an authorized camera send frames for a direction other than the one it registered for."

### Q14: "What happens if one of the four phones runs out of battery or disconnects during peak traffic?"
**Answer:**
> "The system handles this through a multi-tiered resilience protocol:
> 1. **Reconnect Grace Period:** If the socket drops, the session is held open for 5.0 seconds so transient network hiccups do not force re-pairing.
> 2. **Staleness Transition:** If no frames arrive for $>3.0$ seconds, the lane transitions from `LIVE` to `STALE`.
> 3. **Scheduler Self-Healing:** The signal scheduler immediately excludes stale approaches from green-time allocation. The remaining three approaches continue operating dynamically in round-robin sequence without human intervention.
> 4. **All-Camera Loss:** If all four cameras disconnect, the system enters a safe `ALL_RED` state until streams recover."
