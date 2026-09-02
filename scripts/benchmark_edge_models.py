"""Compare edge-detector latency and resource use on identical traffic frames.

This is a runtime benchmark, not an accuracy evaluation. Use evaluate_detector.py
with labelled traffic data before changing the production model.
"""

import argparse
import json
import os
import time
from pathlib import Path

os.environ.setdefault("OMP_WAIT_POLICY", "PASSIVE")
os.environ.setdefault("KMP_BLOCKTIME", "0")

import cv2
import numpy as np
import psutil
import torch
from ultralytics import YOLO

VEHICLE_CLASSES = [1, 2, 3, 5, 7]


def load_frames(source: Path, count: int) -> list[np.ndarray]:
    image = cv2.imread(str(source))
    if image is not None:
        return [image.copy() for _ in range(count)]
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open benchmark video: {source}")
    total = max(1, int(capture.get(cv2.CAP_PROP_FRAME_COUNT)))
    indexes = np.linspace(0, total - 1, count, dtype=int)
    frames: list[np.ndarray] = []
    for index in indexes:
        capture.set(cv2.CAP_PROP_POS_FRAMES, int(index))
        ok, frame = capture.read()
        if ok and frame is not None:
            frames.append(frame)
    capture.release()
    if not frames:
        raise RuntimeError(f"No frames could be read from: {source}")
    return frames


def benchmark(model_name: str, frames: list[np.ndarray], imgsz: int, threads: int,
              conf: float, iou: float, max_det: int) -> dict:
    torch.set_num_threads(threads)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    model = YOLO(model_name)
    predict_args = dict(device="cpu", imgsz=imgsz, conf=conf, iou=iou,
                        max_det=max_det, classes=VEHICLE_CLASSES, verbose=False)
    for frame in frames[: min(3, len(frames))]:
        model.predict(frame, **predict_args)

    process = psutil.Process()
    rss_before = process.memory_info().rss
    cpu_before = sum(process.cpu_times()[:2])
    latencies: list[float] = []
    detections: list[int] = []
    started = time.perf_counter()
    for frame in frames:
        frame_started = time.perf_counter()
        result = model.predict(frame, **predict_args)
        latencies.append((time.perf_counter() - frame_started) * 1000)
        detections.append(len(result[0].boxes) if result else 0)
    wall_seconds = time.perf_counter() - started
    cpu_seconds = sum(process.cpu_times()[:2]) - cpu_before
    rss_after = process.memory_info().rss

    model_path = Path(model_name)
    model_bytes = model_path.stat().st_size if model_path.is_file() else sum(
        item.stat().st_size for item in model_path.rglob("*") if item.is_file()
    ) if model_path.is_dir() else 0
    return {
        "model": model_name,
        "frames": len(frames),
        "imgsz": imgsz,
        "threads": threads,
        "confidence": conf,
        "iou": iou,
        "max_detections": max_det,
        "p50_ms": round(float(np.percentile(latencies, 50)), 2),
        "p95_ms": round(float(np.percentile(latencies, 95)), 2),
        "mean_ms": round(float(np.mean(latencies)), 2),
        "throughput_fps": round(len(frames) / wall_seconds, 2),
        "cpu_seconds_per_frame": round(cpu_seconds / len(frames), 4),
        "rss_after_mb": round(rss_after / 1024**2, 1),
        "rss_delta_mb": round((rss_after - rss_before) / 1024**2, 1),
        "mean_vehicle_detections": round(float(np.mean(detections)), 2),
        "model_size_mb": round(model_bytes / 1024**2, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark edge models on identical traffic frames")
    parser.add_argument("--models", nargs="+", default=["yolo26n.pt", "yolo26s.pt"])
    parser.add_argument("--source", default="tests/fixtures/ultralytics_bus.jpg")
    parser.add_argument("--frames", type=int, default=40)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--conf", type=float, default=0.15)
    parser.add_argument("--iou", type=float, default=0.60)
    parser.add_argument("--max-det", type=int, default=300)
    parser.add_argument("--output", default="docs/benchmarks/edge-models-laptop.json")
    args = parser.parse_args()

    source = Path(args.source)
    frames = load_frames(source, max(5, args.frames))
    results = [benchmark(name, frames, args.imgsz, args.threads,
                         args.conf, args.iou, args.max_det) for name in args.models]
    report = {
        "scope": "Identical local traffic frames; runtime/resource comparison only. Not an accuracy or power-meter benchmark.",
        "source": str(source),
        "vehicle_classes": VEHICLE_CLASSES,
        "results": results,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
