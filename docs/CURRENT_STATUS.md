# Current project status — 10 September 2026

This file is the durable handoff if the Codex conversation is refreshed.

## Active versions

- Backend detector: `yolov8n.pt` at 576 pixels on the laptop, configured in `config/model.py`.
- Tracking: independent ByteTrack state for north, east, south and west.
- Mobile app source: 1.0.7, Android versionCode 8, with WebRTC video and automatic sampled-JPEG fallback.
- Previous stable APK: `C:\Users\ashek\Downloads\traffic-camera-node-preview-1.0.6-arm64.apk`.
- Version 1.0.7 EAS build: `18f12b92-042b-4426-a2f7-78458809169d` (finished).
- Version 1.0.7 APK: `C:\Users\ashek\Downloads\traffic-camera-node-preview-1.0.7-video.apk`.

## Cleanup

Removed 34.03 MB of reproducible or superseded content: YOLO26n/YOLO26s
weights, the old mobile 1.0.2 export, runtime logs, Python/test caches and a
stale Kotlin compiler session. Virtual environments and `node_modules` remain
because they are required to run and build the projects without reinstalling
dependencies. Tracked benchmark inputs/results and YOLOv8n were preserved.
After runtime comparison, the reproducible 12.1 MB ONNX export and temporary
runtime logs were also removed because PyTorch was materially faster on this
laptop. The export script remains available for testing other target hardware.

## Fresh detector comparison

The same tracked real traffic-photo crop was inferred 30 times at 640 pixels,
four CPU threads, confidence 0.15 and IoU 0.60. This measures warmed detector
runtime and resource cost; it is not labelled accuracy or electrical power.

| Metric | YOLOv8n (current) | YOLO26s (previous) | Change |
|---|---:|---:|---:|
| Mean inference | 73.97 ms | 185.95 ms | 60.2% lower |
| p50 inference | 54.50 ms | 113.90 ms | 52.2% lower |
| Throughput | 13.52 FPS | 5.38 FPS | 2.51× |
| CPU seconds/frame | 0.1734 | 0.4661 | 62.8% lower |
| Weight size | 6.25 MB | 19.48 MB | 67.9% smaller |
| Mean detections on this image | 59 | 22 | descriptive only |

More detections do not prove better accuracy. A labelled moving-video set is
still required to measure precision, recall, count error and ByteTrack ID
switches. Full benchmark data is in
`docs/benchmarks/yolov8n-vs-yolo26s-final.json`.

## Four-camera video validation

Four simultaneous QR-authenticated WebRTC peers passed negotiation, heartbeat,
direction isolation, video decode, batched YOLO, per-lane ByteTrack and frame
acknowledgement using four different real road photographs. With the 576-pixel
laptop profile, every lane processed 59-60 updates in 20 seconds (2.95-3.0 FPS).
Direction p95 server latency was 633-679 ms, p95 batched inference was 472-509 ms,
and p95 queue wait was 217-226 ms. Raw results are in
`docs/benchmarks/four-webrtc-runtime.json`.

The former serialized JPEG path produced about 0.4-0.5 FPS per lane with p95 ACK
latency of 2.24-2.30 seconds. The new latest-frame coordinator and four-frame
inference batch meet the software target of p95 below 750 ms in this local
four-peer replay. This does not measure physical Wi-Fi or phone latency.

A second server-focused run offered two real-image frames per second per lane.
All 164 frames were acknowledged, p95 server latency was 416-544 ms, and the
server used a median 1.41 CPU cores and about 458 MB RSS. Its raw results are in
`docs/benchmarks/pt576-batch-four-2fps.json`.

Scheduler tests serve each occupied lane once in clockwise order, apply bounded
demand-dependent green durations, skip empty lanes and prevent starvation of a
low-demand occupied lane. USB, video-file, RTSP and Picamera2 sources can now use
the same coordinator through `TRAFFIC_SOURCES_JSON`.

## Startup and integration

YOLO now warms its predictor during backend startup, before mobile camera
sessions are accepted. This moves the one-time several-second initialization
cost out of the first camera frame. A four-camera smoke test passed registration,
processing, independent stale-camera handling and system stop/start with YOLOv8n.

The 1.0.7 APK still needs physical portrait and both-landscape testing on the target
phone. The sender removes the RTP orientation extension so encoded pixels arrive
upright at the backend, but desktop peers cannot prove phone-specific camera
behavior. Raspberry Pi performance cannot be inferred from the laptop benchmark;
fine-tune on labelled traffic data, export YOLOv8n to NCNN, then benchmark the
actual Pi before controlling hardware.
