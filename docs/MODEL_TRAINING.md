# Real-traffic model preparation

The deployment candidate is **YOLO26n fine-tuned on UVH-26**, then exported to
NCNN for Raspberry Pi. Generic YOLO26s COCO weights are the higher-recall laptop
bootstrap model;
they are not the final detector for Indian traffic.

## Why this model and dataset

Ultralytics reports YOLO26n at 40.9 COCO box mAP with 2.4 million fused
parameters, and its Raspberry Pi guide measures the YOLO26n NCNN export at about
67 ms inference per 640-pixel image on a Raspberry Pi 5. NCNN was the fastest of
the formats in that published Pi test:

- https://docs.ultralytics.com/models/yolo26/
- https://docs.ultralytics.com/guides/raspberry-pi/

The official IISc UVH-26 release is better matched to this project than COCO. It
contains 26,646 real 1080p frames from about 2,800 Bengaluru traffic cameras and
1.8 million boxes across 14 vehicle classes. Those classes include bicycles,
two-wheelers, three-wheelers, LCVs, vans, buses and trucks. The dataset is CC BY
4.0 and is about 90 GB:

- https://www.iisc.ac.in/events/aim-iisc-announces-public-release-of-uvh-26-dataset-and-vision-models-for-indian-urban-traffic/
- https://huggingface.co/datasets/iisc-aim/UVH-26

UVH-26 does not label ambulances, fire engines, or police vehicles separately.
Emergency priority therefore remains a control input awaiting a separately
labelled, consented dataset. It must not be inferred from an ordinary car label.

## Prepare and train

Download the official `UVH-26-Train` and `UVH-26-Val` release outside Git. Then:

```powershell
.\.venv\Scripts\python.exe scripts\prepare_uvh26.py --source D:\datasets\UVH-26 --output datasets\uvh26
.\.venv\Scripts\python.exe scripts\train_traffic_model.py --data datasets\uvh26\traffic.yaml --model yolo26n.pt --device 0
.\.venv\Scripts\python.exe scripts\evaluate_detector.py --data datasets\uvh26\traffic.yaml --model outputs\training\yolo26n-uvh26\weights\best.pt --device 0 --output docs\benchmarks\yolo26n-uvh26-accuracy.json
.\.venv\Scripts\python.exe scripts\export_edge_model.py --model outputs\training\yolo26n-uvh26\weights\best.pt --format ncnn
```

`prepare_uvh26.py` converts COCO boxes to YOLO labels and uses hard links by
default, avoiding another 90 GB image copy. Keep the official validation split
untouched. Reserve a labelled local camera test set for final calibration.

For a quick laptop comparison, four official UVH-26 validation frames with 41
labelled vehicles were tested on 2 September. The previous YOLO26n, 640 px,
confidence 0.35 configuration produced 13 detections. YOLO26s at 640 px with
confidence 0.15 produced 38 candidates; class-agnostic IoU matching at 0.5 measured
precision 0.763, recall 0.707 and F1 0.734. Mean detector time was about 89 ms after
warm-up on this laptop. This small calibration sample does not replace complete
validation or local-camera testing.

## Required evidence before Raspberry Pi control testing

- Report precision, recall, mAP50, mAP50-95, and per-class AP on UVH-26 validation.
- Add a labelled local set from the actual fixed camera height and angle, covering
  daylight, night, rain, glare, occlusion, dense queues, and empty approaches.
- Measure count error per approach and failure cases, not only image-level mAP.
- Run four-source load tests with `scripts/benchmark_runtime.py --images` and
  record p50/p95 ACK, queue, inference, CPU, RSS, dropped frames, and temperature.
- On Raspberry Pi, compare 640 and 480 input sizes. Accept 480 only if the local
  small-object and two-wheeler recall loss is acceptable.
- Keep the signal output simulated until fail-safe hardware, yellow/all-red
  timing, watchdog behavior, and applicable traffic-engineering rules are tested.

Suggested project gates are macro mAP50-95 at least 0.50, no safety-relevant
vehicle class below 0.70 recall on the local set, count MAE below 10%, four-camera
p95 processed ACK below 750 ms at 2 samples/s per camera, no unbounded RSS growth,
and no lane starvation. These are engineering targets, not current measured claims.
