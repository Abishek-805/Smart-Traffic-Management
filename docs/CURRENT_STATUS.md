# Current project status — 9 September 2026

This file is the durable handoff if the Codex conversation is refreshed.

## Active versions

- Backend detector: `yolov8n.pt`, configured in `config/model.py`.
- Tracking: independent ByteTrack state for north, east, south and west.
- Mobile app: 1.0.6, Android versionCode 7.
- APK: `C:\Users\ashek\Downloads\traffic-camera-node-preview-1.0.6-arm64.apk`.
- EAS build: `359acb9f-2cb6-43a9-9512-3e34c55476b7` (finished).

## Cleanup

Removed 34.03 MB of reproducible or superseded content: YOLO26n/YOLO26s
weights, the old mobile 1.0.2 export, runtime logs, Python/test caches and a
stale Kotlin compiler session. Virtual environments and `node_modules` remain
because they are required to run and build the projects without reinstalling
dependencies. Tracked benchmark inputs/results and YOLOv8n were preserved.

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

## Four-camera validation

Four simultaneous authenticated camera clients passed registration, heartbeat,
direction isolation, detection and telemetry checks using different real road
images. Scheduler validation served North, East, South and West in clockwise
order for 60, 12, 54 and 51 seconds respectively; the low-demand East lane was
not starved, and an empty East lane was skipped.

The current CPU runtime does not meet the desired four-camera latency target on
dense scenes. At two offered FPS per camera it processed about 0.4-0.5 FPS per
lane and direction p95 ACK latency was 2.24-2.30 seconds. At 0.5 offered FPS per
camera, every lane sustained 0.5 processed FPS, but synchronized arrivals still
produced p95 latency of 1.67-1.92 seconds. Details and raw results are in
`docs/benchmarks/FOUR_CAMERA_VALIDATION_2026-09-09.md` and the adjacent JSON
files. The shared serialized inference worker is the limiting component.

## Startup and integration

YOLO now warms its predictor during backend startup, before mobile camera
sessions are accepted. This moves the one-time several-second initialization
cost out of the first camera frame. A four-camera smoke test passed registration,
processing, independent stale-camera handling and system stop/start with YOLOv8n.

The APK still needs physical portrait and both-landscape testing on the target
phone. Raspberry Pi performance cannot be inferred from the laptop benchmark;
fine-tune on labelled traffic data, export YOLOv8n to NCNN, then benchmark the
actual Pi before controlling hardware.
