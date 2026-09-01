# Four-camera optimization report — 1 September 2026

## Edge model A/B

YOLO26n was selected over YOLO11n after a controlled current-machine comparison.
Both models processed 324/324 frames across four simultaneous 4 FPS clients. The
mean direction inference p95 was 62.84 ms for YOLO26n and 65.20 ms for YOLO11n;
process CPU p50 was 140.6% versus 147.65% of one core, and RSS p50 was 308.69 MB
versus 394.78 MB. Mean ACK p95 was slightly higher for YOLO26n (211.87 ms versus
206.18 ms) and preview p95 was effectively tied (267.65 ms versus 265.35 ms).

This load test establishes throughput and resource behavior, not accuracy. An
isolated bus-image comparison detected the same one vehicle and measured 83.79 ms
mean PyTorch latency for YOLO26n versus 109.67 ms for YOLO11n. Actual traffic
accuracy still requires the labelled-data gate in `scripts/evaluate_detector.py`.

## What was measured

The reproducible benchmark opens four camera WebSockets, one for each direction,
replays the supplied 640-pixel local clips at 4 FPS per camera, consumes all four
MJPEG previews, sends heartbeats, and records processed-frame ACK, server queue,
inference, preview-byte arrival, process CPU and RSS.

This is a localhost transport/load test. It does **not** measure Wi-Fi, physical
phone capture/encode, screen rendering, battery watts, or model accuracy. The
supplied direction clips produced zero vehicle detections, so they test four-feed
throughput and isolation rather than detector quality.

## Before and after

| Measurement | Baseline, 20 s | Final, 60 s | Change |
| --- | ---: | ---: | ---: |
| Offered/acknowledged rate | 4.10 / 4.10 FPS per camera | 4.00 / 4.00 FPS per camera | No loss |
| Frames acknowledged | 328 / 328 | 960 / 960 | 100% in both |
| Mean of direction ACK p95 | 163.3 ms | 138.5 ms | 15.2% lower |
| Mean of direction server p95 | 162.7 ms | 137.9 ms | 15.2% lower |
| Mean of direction inference p95 | 46.6 ms | 38.2 ms | 18.0% lower |
| Mean of direction preview-arrival p95 | 229.7 ms | 213.6 ms | 7.0% lower |
| Process CPU p50 (one core = 100%) | 1181.8% | 107.8% | 90.9% lower |
| Approx. share of 16 logical CPUs | 73.9% | 6.7% | 67.2 points lower |
| Process RSS p50 | 980.8 MB | 392.0 MB | 60.0% lower |
| RSS change during measured window | 10.25 MB / 20 s | 1.36 MB / 60 s | Stable after warm-up |
| Process threads after load | 107 observed | 29 observed | 78 fewer |

Raw records are in `docs/benchmarks/baseline-four-4fps.json` and
`docs/benchmarks/optimized-four-4fps-final-60s.json`. The baseline and final run
used the same laptop, model weights, 640-pixel images and four replay sources.

## Implemented changes

- Use four PyTorch CPU inference threads on this i5-13450HX. The separate
  repeatable inference test found four faster than one, two or eight while
  returning the same reference-image boxes within tolerance.
- Disable active OpenMP waiting and set OpenCV to one internal thread.
- Execute all serialized pipeline work on one persistent native worker. This
  prevents PyTorch/OpenCV workspaces from being allocated across asyncio's large
  default pool and produced the stable final RSS result.
- Keep one latest frame per direction and wake workers with events instead of
  polling. Camera queues cannot grow with delayed inference.
- Send `FRAME_ACK` with frame ID, total server time, queue time and inference time.
  The mobile app permits one processed frame in flight and recovers after a lost
  ACK timeout.
- Preserve 640-pixel model input and FP32 weights. No unmeasured quantization,
  frame-size reduction or model substitution was used to obtain the result.
- Encode annotated browser previews at JPEG quality 80 to reduce viewer traffic;
  this does not alter detector input.
- Bound scheduler diagnostic history and validate camera timestamps before use.

## Traffic-control rules now enforced

- Only fresh camera approaches are eligible for a phase.
- An empty/stale intersection falls back to all-red.
- Green is followed by yellow and a one-second all-red clearance before another
  phase is selected in software.
- Fresh emergency demand preempts normal/starvation selection. The current COCO
  model does not identify emergency vehicles, so this is a tested control rule for
  a future detector input rather than a claimed live capability.
- Fresh demand waiting for three completed phases is served to bound starvation.
- Minimum/maximum green settings remain enforced, and paused or unavailable inputs
  never appear green in telemetry.

These rules are software/simulation results. The ESP32 and real signals were not
connected, so physical clearance timing and fail-safe behavior remain release gates.

## Accuracy and physical-device gates

Detector efficiency is measured; detector accuracy is not yet quantifiable because
no labelled project dataset was supplied. Run:

```powershell
.venv\Scripts\python.exe scripts\evaluate_detector.py --data path\to\traffic.yaml --model yolo11n.pt --imgsz 640
```

It writes precision, recall, mAP50, mAP50-95, per-class mAP, speed and Ultralytics
evaluation artifacts. Use representative day/night, rain, occlusion, motorcycle,
bus and truck labels from the intended camera positions. Fine-tune or change
thresholds only from those results.

A development build or installed APK on the target phone is still required to
verify visible flashing, camera permission/lifecycle, Wi-Fi frame RTT, temperature,
battery drain and four-phone endurance. Expo Go cannot run the native
VisionCamera/Nitro path used here.
