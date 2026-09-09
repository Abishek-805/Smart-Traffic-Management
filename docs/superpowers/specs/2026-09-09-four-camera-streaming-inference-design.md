# Four-Camera Streaming Inference Design

**Date:** 2026-09-09

## Objective

Improve four-camera throughput and latency while preserving accurate, fair traffic decisions. The same perception pipeline must accept QR-paired Android cameras during laptop testing and direct, USB, or RTSP cameras during Raspberry Pi deployment.

## Current limitation

Android nodes capture JPEG samples, base64-encode them, and send JSON messages over authenticated WebSockets. The backend keeps a latest-frame slot per direction, but four independent lane workers submit frames to one serialized executor and one model call at a time. Dense four-camera testing at two offered frames per second per lane processes only about 0.4-0.5 frames per second per lane, with p95 acknowledgement latency near 2.3 seconds.

Changing the wire format to H.264 video would reduce bandwidth, but it would not reduce YOLO compute. On a Raspberry Pi running both capture and inference, encoding local camera frames to H.264 and decoding them again would waste resources. The primary optimization is coordinated newest-frame batching, followed by an efficient model runtime. Video transport remains useful for remote phones and IP cameras.

## Selected architecture

### 1. Transport-independent frames

All inputs produce a common `CameraFrame` containing direction, frame ID, BGR image, capture timestamp, receive timestamp, dimensions, rotation metadata, and source kind. Mobile WebSocket JSON JPEG remains supported. Binary WebSocket JPEG is added as an optional protocol after registration; its small metadata header carries the same authenticated identity and timing information. Direct Picamera2, USB, file, and RTSP sources feed decoded frames through the same interface.

The detector never depends on QR, WebSocket, RTSP, or camera-library details.

### 2. Latest-frame coordinator

One coordinator owns four bounded direction slots. A new frame replaces an older unprocessed frame for the same lane. The coordinator wakes when a slot changes, waits no more than 40 ms to collect other fresh directions, and forms a batch of one to four frames. Frames older than 2.5 seconds are rejected before inference.

Only one batch is in flight on a CPU model runtime. This preserves bounded memory and prevents an input stream from building a queue. Batch results are mapped back to their source direction and frame ID.

### 3. Batched detection and independent tracking

`ModelManager.predict_batch(frames)` invokes YOLO once with a list of current frames. `VehicleDetector.detect_batch(frames)` converts each corresponding result to the existing detection representation. The traffic pipeline applies the result to a separate ByteTrack, lane manager, vehicle-state manager, count stabilizer, and telemetry record for each direction.

Track state is never shared across directions. Frames processed between detector observations may advance the existing per-lane Kalman prediction, but predicted boxes do not create vehicles or refresh detection freshness. Scheduling uses confirmed, recent observations.

The batch coordinator uses an adaptive detector interval. It starts at two detector samples per second per active lane, measures batch service time and frame age, and reduces offered detection cadence when the backend cannot keep up. It never buffers old frames to preserve nominal FPS.

### 4. Camera modes

**Laptop with Android phones:** The camera preview runs continuously. The application sends selected newest frames at the server-requested rate. Binary JPEG is preferred when supported; the existing base64 JSON path remains a compatibility fallback. Full 30 FPS video is unnecessary for a detector targeting one to four observations per second per lane.

**Raspberry Pi with local cameras:** Picamera2 or USB sources provide decoded frames directly. No network video encode/decode is performed. Capture can run at camera rate while the coordinator selects current frames for inference.

**Remote mobile or IP cameras:** RTSP/H.264 or a future WebRTC adapter may decode continuously into the same latest-frame slots. Decode queues must drop old frames. Transport selection does not change detector or scheduler behavior.

### 5. Model deployment

YOLOv8n remains the laptop baseline because the local comparison found materially lower latency, CPU time, and model size than the previous YOLO26s profile. Raspberry Pi CPU deployment uses a fine-tuned YOLOv8n NCNN export, tested at 640 and 480 input sizes. An accelerator such as Raspberry Pi AI HAT+ is the preferred option when four simultaneous streams must sustain higher rates.

No model is declared accurate from unlabelled photographs. Model selection requires labelled moving traffic video covering cars, buses, trucks, motorcycles, bicycles, auto-rickshaws, occlusion, night scenes, rain, portrait, and both landscape orientations.

## Backpressure and failure handling

- Each lane owns exactly one pending frame slot.
- Replaced, stale, malformed, unauthorized, and decode-failed frames increment distinct counters.
- A failing source cannot block other directions.
- Camera heartbeats remain independent of inference acknowledgements.
- A disconnected lane becomes stale and is excluded from fresh scheduling data.
- Batch failure reports an error for affected frames and leaves the previous confirmed traffic state marked stale rather than inventing zero traffic.
- The scheduler retains clockwise service, minimum and maximum green bounds, empty-lane release, maximum-wait fairness, and emergency preemption.

## Observability

Per lane telemetry reports capture rate, accepted-frame rate, processed rate, detector rate, tracker rate, frame age, decode time, batch wait, batch size, inference time, total server time, replacements, and failures. Runtime telemetry reports aggregate batch throughput, CPU, memory, runtime/model name, and active source type.

## Compatibility

Existing version 1.0.6 mobile clients remain functional through the JSON/base64 protocol. QR payloads, session tokens, direction ownership, system start/stop, telemetry WebSocket, MJPEG dashboard previews, and REST endpoints retain their current behavior. Binary mobile frames and direct/RTSP sources are additive.

## Validation

Automated tests must cover:

1. Four latest-frame slots remain bounded and isolated.
2. A batch result returns to the correct node, direction, and frame ID.
3. Each lane maintains independent ByteTrack IDs.
4. A slow or disconnected lane does not block the other three.
5. Stale frames never enter a model batch.
6. Base64 and binary JPEG inputs normalize portrait and landscape frames identically.
7. Scheduler ordering, fairness, empty-lane behavior, green bounds, and emergency preemption remain unchanged.
8. Direct/file/RTSP adapters reconnect and discard stale decoded frames.

The reproducible benchmark uses four concurrent streams of real moving traffic video and compares the existing serial baseline with the batched path. It records p50/p95 acknowledgement latency, frame age, batch size, processed FPS, CPU, RSS, detection count stability, and dropped/replaced frames. The laptop target is p95 processed-frame age below 750 ms at two offered samples per second per camera. Accuracy acceptance requires a labelled set: per-class precision/recall, count mean absolute error, and ByteTrack ID switches. Raspberry Pi performance and power are measured on the actual board.

## Out of scope for this iteration

- Replacing QR pairing or authentication.
- Browser playback of the original full-rate camera video.
- Cloud streaming or internet-facing deployment.
- Claiming Raspberry Pi performance without an on-device benchmark.
- Automatically controlling physical lights before labelled accuracy, fail-safe, and hardware tests pass.

