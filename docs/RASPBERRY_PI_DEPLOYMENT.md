# Raspberry Pi detector deployment

## Selected model path

The retained fallback is **YOLO11n at 640 pixels**. It is a mature option and
already improves on YOLOv8n: Ultralytics reports 39.5 COCO box mAP, 2.6 million
parameters and 6.5 GFLOPs for YOLO11n, versus 37.3 mAP, 3.2 million parameters and
8.7 GFLOPs for YOLOv8n.

The selected laptop model and Raspberry Pi candidate is **YOLO26n**. Use PyTorch
for current laptop validation and export it to NCNN for Raspberry Pi CPU testing.
Ultralytics' Raspberry Pi 5 benchmark reports YOLO26n
at 128.42 ms per image with ONNX versus about 147 ms for YOLO11n, with slightly
higher COCO mAP. NCNN is the runtime Ultralytics recommends for ARM edge devices.
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
python scripts/export_edge_model.py --model yolo26n.pt --format ncnn --imgsz 640
cp .env.example .env
```

Set these values in `.env`:

```dotenv
YOLO_MODEL_NAME=models/yolo26n_ncnn_model
YOLO_INPUT_SIZE=640
YOLO_CPU_THREADS=4
YOLO_MAX_DETECTIONS=100
YOLO_DEVICE=cpu
```

Use the mobile **Low power** profile at 2 sampled frames per second. Four cameras
then request at most about eight inferences per second, while processed-frame ACK
backpressure prevents queues from growing. If p95 frame age exceeds the control
limit, try `YOLO_INPUT_SIZE=512` and re-run labelled accuracy evaluation before
keeping that reduction.

## Accuracy gate

The replay and load tests measure latency and reliability; they cannot establish
precision or recall. Evaluate both candidates on labelled camera images from the
actual mounting height, road geometry, lighting, rain, and local vehicle mix:

```bash
python scripts/evaluate_detector.py --data datasets/traffic.yaml --model yolo11n.pt --output docs/benchmarks/yolo11n-accuracy.json
python scripts/evaluate_detector.py --data datasets/traffic.yaml --model yolo26n.pt --output docs/benchmarks/yolo26n-accuracy.json
python scripts/benchmark_edge_models.py --models yolo11n.pt yolo26n.pt --source videos/traffic.mp4
```

Keep the candidate only if per-class recall for motorcycle, car, bus, and truck,
queue count error, and p95 inference latency all meet the junction's acceptance
limits. Fine-tune the nano model on local data when auto-rickshaws, occlusion, or
distant motorcycles are missed; generic COCO weights do not define an auto-rickshaw
class.

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
