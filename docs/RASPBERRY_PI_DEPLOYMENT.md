# Raspberry Pi detector deployment

## Selected model path

The laptop test profile and Raspberry Pi candidate now use **YOLOv8n**. Fine-tune
it on UVH-26, then export the trained nano model to NCNN for Raspberry Pi CPU
testing. NCNN is the runtime Ultralytics recommends for ARM edge devices.
It must still pass the project's labelled traffic validation before any public-road
deployment; current generic COCO weights have not been validated on local traffic.

Do not use YOLOv8s, YOLO11s, or larger models on a CPU-only Pi for four approaches.
Their extra compute reduces freshness more than it helps this controller. A traffic
specific fine-tuned nano model is more valuable than increasing the generic model size.

## CPU-only Raspberry Pi 5

Use 64-bit Raspberry Pi OS, active cooling, and a supported Python version. Create
the environment and install the project's requirements, then export on the Pi so
the NCNN files match its runtime:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/export_edge_model.py --model outputs/training/yolov8n-uvh26/weights/best.pt --format ncnn --imgsz 640
cp .env.example .env
```

Set these values in `.env`:

```dotenv
YOLO_MODEL_NAME=models/best_ncnn_model
YOLO_INPUT_SIZE=512
YOLO_CPU_THREADS=4
YOLO_MAX_DETECTIONS=300
YOLO_CONFIDENCE_THRESHOLD=0.08
DETECTOR_FPS=1.0
TRACK_HIGH_THRESHOLD=0.15
TRACK_LOW_THRESHOLD=0.08
NEW_TRACK_THRESHOLD=0.15
YOLO_DEVICE=cpu
```

Start a CPU-only Pi at one detector update per second per lane and 512 pixels.
The coordinator always keeps only the newest frame, so overload reduces update
rate instead of growing latency. Try 416 pixels only after a labelled comparison.
For sustained four-camera rates near the laptop profile, use the AI HAT+ path
below rather than assuming a Pi CPU can match this laptop.

## Accuracy gate

The replay and load tests measure latency and reliability; they cannot establish
precision or recall. Evaluate both candidates on labelled camera images from the
actual mounting height, road geometry, lighting, rain, and local vehicle mix:

```bash
python scripts/evaluate_detector.py --data datasets/uvh26/traffic.yaml --model outputs/training/yolov8n-uvh26/weights/best.pt --output docs/benchmarks/yolov8n-uvh26-accuracy.json
python scripts/benchmark_runtime.py --pid SERVER_PID --images datasets/uvh26/images/val --seconds 60 --fps 2 --output docs/benchmarks/pi-four-real.json
```

Keep the candidate only if per-class recall across all 14 UVH-26 vehicle classes,
queue count error, and p95 inference latency all meet the junction's acceptance
limits. Fine-tune the nano model on local data when auto-rickshaws, occlusion, or
distant motorcycles are missed; generic COCO weights do not define an auto-rickshaw
class. Full preparation and validation steps are in `docs/MODEL_TRAINING.md`.

## Hardware acceleration

For sustained four-camera real-time operation and lower CPU load, a Raspberry Pi 5
with an AI HAT+ is the stronger deployment. Raspberry Pi's official stack offloads
object detection to the Hailo NPU; the 13 TOPS AI HAT+ is enough for vision workloads.
Use the official precompiled YOLOv8 pipeline for an initial hardware check, or compile
the validated custom traffic model with the matching Hailo toolchain. Hailo runtime,
firmware, and compiled model versions must match.

Sources:

- https://docs.ultralytics.com/models/yolo11/
- https://docs.ultralytics.com/models/yolov8/
- https://docs.ultralytics.com/guides/raspberry-pi/
- https://docs.ultralytics.com/integrations/ncnn/
- https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html
- https://www.raspberrypi.com/documentation/computers/ai.html
