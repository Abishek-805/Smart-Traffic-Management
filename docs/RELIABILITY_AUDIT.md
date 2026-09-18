# Reliability, Fault-Tolerance & Failure Injection Audit

**Date:** 18 September 2026  
**Audited Repositories:**  
1. `Smart-Traffic-Management` (Backend Engine)  
2. `Traffic_Camera_App` (Mobile Node)  
**Classification Standard:** Software-Verified Failure Injection and Edge-Case Recovery.

---

## 1. Reliability Architecture & Invariants

A critical requirement of traffic signal infrastructure is **fail-safe operation**: software faults, network drops, or sensor loss must never lead to conflicting green signals across intersecting lanes.

The system enforces six core software reliability invariants:

1. **Mutual Exclusion (Never Multi-Green):** At most one lane direction may hold the `GREEN` or `YELLOW` state at any timestamp. All opposing approaches display `RED`.
2. **Safe All-Red Fallback:** If camera streams go stale or communication fails, the intersection commands a safe `ALL_RED` state.
3. **Fail-Closed Software Logic:** If physical microcontroller mode (`HARDWARE=esp32`) is configured but serial communication fails, the engine halts automatic cycles and forces an `ALL_RED` state rather than silently faking simulation. Physical hardware operation itself remains unvalidated.
4. **Bounded Memory & Execution:** Queues, executors, and log buffers are strictly bounded. Unprocessed frames are dropped rather than accumulated.
5. **Fault Containment:** Uncaught errors inside AI detection, tracking, or network parsing increment error counters and recover cleanly without terminating the background ticker under tested failure scenarios.
6. **Graceful Reconnection Window:** Temporary Wi-Fi socket drops do not immediately invalidate device pairing, allowing client reconnection within 10.0 seconds (`HEARTBEAT_TIMEOUT_SEC = 10.0s`).

---

## 2. Failure Injection Test Matrix

The test suite systematically simulates network, camera, hardware, and runtime faults:

| Scenario / Fault Injected | Expected System Reaction | Test File & Verification | Status |
|---|---|---|---|
| **Camera Socket Loss** | Session preserved for 10.0s; frames paused; scheduler skips stale lane. | `test_unexpected_socket_loss_preserves_short_reconnect_window` | `VERIFIED` |
| **Expired Reconnect Attempt** | Reconnection after heartbeat expiry (>10s) rejected with `UNAUTHORIZED_SESSION`. | `test_expired_tokens_cannot_revive_sessions` | `VERIFIED` |
| **Camera Stale Frame (>2.5s)** | Frame dropped before AI decoding; `dropped` stage counter incremented. | `test_observation_semantics.py` / `frame_coordinator.py` | `VERIFIED` |
| **All Cameras Disconnected** | Intersection enters `ALL_RED` state; timer set to 0; reason logged as "Waiting for fresh camera frames". | `test_freshness_is_per_direction_and_idle_is_not_green` | `VERIFIED` |
| **ESP32 COM Port Missing** | `HardwareConnectionState.ERROR`; `system_running = False`; signal switches to `ALL_RED`. | `test_requested_esp32_failure_forces_safe_all_red_and_visible_error` | `VERIFIED` (Software logic) |
| **ESP32 Serial Write Failure** | PySerial exception caught; `last_error` recorded; system pauses; command rejected. | `test_hardware_transmission_failure_pauses_runtime_and_forces_all_red` | `VERIFIED` (Software logic) |
| **ESP32 Port Reconnect** | Closed stale serial handle, reconnects cleanly once port reappears. | `test_esp32_reconnect_recovers_after_initial_failure` | `VERIFIED` (Software logic) |
| **AI Runtime Exception in Ticker** | Exception logged at ERROR; `frame_processing_errors` counter incremented; ticker continues. | `test_runtime_iteration_logs_exception_and_increments_counter` | `VERIFIED` |
| **Malformed Frame Base64** | `cv2.imdecode` returns None; `decode_failed` counter incremented; no crash. | `test_local_sources.py` | `VERIFIED` |
| **Protocol Version Mismatch** | Protocol server returns `PROTOCOL_VERSION_MISMATCH` with correlation ID. | `test_websocket_protocol_version_mismatch` | `VERIFIED` |
| **WebRTC ICE Gathering Timeout** | Times out at 1500 ms; cleans up tracks; notifies user with actionable network advice. | Mobile `WebRTCVideoSession.ts` | `VERIFIED` |
| **Mobile Camera Crash Loop** | Bounded to max 3 restarts within 30s window; stops capture on 5th consecutive failure. | Mobile `CameraCaptureService.ts` | `VERIFIED` |

---

## 3. Detailed Fault-Containment Mechanics

### 3.1 Fault-Contained Runtime Ticker
In `server/runtime.py`, the core orchestration loop executes every 500 ms. An uncaught exception in image processing or analytics is isolated:

```python
async def run_runtime_iteration(ctx, message_handler, publish=None) -> bool:
    try:
        # Step sessions, step pipeline, update snapshot
        ...
        return True
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        ctx.frame_processing_errors += 1
        logger.error("Runtime ticker failed (%s): %s", type(exc).__name__, exc)
        logger.debug("Runtime ticker traceback", exc_info=True)
        if ctx.control_manager:
            status = ctx.control_manager.esp32_interface.get_status()
            if not hardware_is_safe_to_run(status):
                ctx.system_running = False
        return False
```
- **Fault Containment:** Increments `frame_processing_errors`. The operations dashboard monitors this counter and flags red if errors escalate.
- **Fail-Safe Check:** Inspects hardware safety on every caught exception and halts automatic cycling if hardware becomes unsafe.

### 3.2 Dynamic Approach Exclusion (Starvation and Stale Skips)
In `ai/signal/signal_scheduler.py`:
- Approaches are evaluated based on freshness:
  ```python
  demand = [s for s in result.scores if key(s) in fresh_lanes and lane_stats.get(key(s)) and lane_stats[key(s)].raw_count > 0]
  ```
- If a camera drops offline (no frame for $>3.0$ seconds) or reports 0 vehicles, the scheduler skips it entirely without wasting green time.
- If all cameras drop offline, the engine outputs `ALL_RED` until valid streams re-register.
- Transition timings: fixed 3.0s Yellow (`YELLOW_SEC = 3`), followed by 2.0s All-Red clearance (`ALL_RED_SEC = 2`).

### 3.3 Tracking & Queue Inactivity Timeouts
In `config/traffic.py`:
- `QUEUE_MOTION_THRESHOLD_PX_SEC = 15.0 px/s`: Motion below 15 px/s for 10 consecutive frames triggers queue status.
- `TRACK_REMOVAL_GRACE_SEC = 1.8s`: Grace period tolerates frame arrival jitter before marking a track lost.
- `TRACK_EXPIRATION_TIMEOUT_SEC = 4.0s`: Hard timeout purges lost tracks after 4 seconds of inactivity.

---

## 4. Mobile Node Resilience (`traffic-camera-app`)

1. **Native Error Boundary:** Wrapped in `AppErrorBoundary.tsx`. If a native component or React tree crashes, it renders a fallback recovery UI with an active "Restart Application" button rather than terminating Android process.
2. **WebRTC to JPEG Fallback:** If WebRTC media track negotiation fails (due to symmetric NAT or firewall blocks), the app gracefully falls back to serialized JPEG snapshot transmission.
3. **Orientation Self-Healing:** Regardless of whether the Android device is held in portrait, landscape-left, landscape-right, or inverted, orientation metadata is transmitted with each frame and corrected via OpenCV matrix rotation on the server.

---

## 5. Reliability Audit Verdict

- **Fault Containment:** `VERIFIED` under tested failure scenarios (no unhandled exceptions can terminate background ticker).
- **Fail-Closed Logic:** `VERIFIED` in software (strict all-red transition on camera or hardware error).
- **Physical Hardware Safety:** `UNVALIDATED` (physical ESP32 relays and optical signal heads have not been tested under load).
