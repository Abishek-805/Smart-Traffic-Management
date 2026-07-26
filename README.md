# Smart Traffic Management System - Sprint 1: Camera & YOLO Detection

An enterprise-grade, modular computer vision pipeline for real-time traffic video processing, vehicle detection (cars, buses, trucks, motorcycles), and performance HUD analytics powered by **YOLO11** and **OpenCV**.

---

## 🌟 System Architecture Overview

```
                      Traffic Video Stream
                              │
                              ▼
                      CameraManager Ingestion
                              │
                              ▼
                     VehicleDetector Engine
                        (YOLO11 Vision)
                              │
                              ▼
                      Detection Dataclass
                  (Class, BBox, Confidence, Time)
                              │
                              ├────────► BaseTracker Interface (Sprint 2 Ready)
                              │
                              ▼
                      Visualizer Engine
                 (Bounding Boxes & HUD Metrics)
                              │
            ┌─────────────────┴─────────────────┐
            ▼                                   ▼
   OpenCV Display Window              Timestamped Video Saver
 (FPS + Latency Metrics)            (outputs/detection_*.mp4)
```

---

## 📁 Repository Structure

```
smart-traffic-management/
│
├── config/                  # Modular system configurations
│   ├── __init__.py
│   ├── model.py             # Model choice (yolo11n.pt), confidence thresholds
│   ├── paths.py             # System paths & timestamped output generators
│   ├── ui.py                # Visual aesthetics, class color palette, font sizing
│   └── traffic.py           # COCO vehicle class mappings (car, motorcycle, bus, truck)
│
├── ai/                      # Computer vision & processing core
│   ├── camera/
│   │   └── camera_manager.py # Ingestion layer (OpenCV VideoCapture lifecycle)
│   ├── models/
│   │   └── model_manager.py  # Model manager for YOLO weights auto-download & inference
│   ├── detection/
│   │   ├── detection_types.py# Immutable Detection dataclass with temporal metadata
│   │   └── detector.py       # Pure vehicle inference engine (no UI rendering)
│   ├── tracking/
│   │   └── base_tracker.py   # Abstract BaseTracker interface for Sprint 2 ByteTrack
│   ├── visualization/
│   │   └── visualizer.py     # Renderer for bounding boxes, badges, HUD, and VideoWriter
│   ├── pipeline/
│   │   └── traffic_pipeline.py# Orchestrator chaining Ingestion -> Vision -> UI
│   └── utils/
│       ├── logger.py         # Multi-target logger (application.log, errors.log)
│       └── statistics.py     # FPS & inference latency monitor
│
├── videos/
│   ├── traffic.mp4           # Input traffic video
│   └── generate_sample_video.py # Synthetic video generator utility
├── models/                   # Auto-downloaded model weights (yolo11n.pt)
├── outputs/                  # Exported detection videos (detection_YYYYMMDD_HHMMSS.mp4)
├── logs/                     # Application & error log files
│
├── main.py                   # Main entry point
├── requirements.txt          # Python dependencies
└── README.md                 # System documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites & Virtual Environment

Ensure you have Python 3.9+ installed.

```bash
# Clone or navigate to directory
cd smart-traffic-management

# Install required dependencies
pip install -r requirements.txt
```

### 2. Verify YOLO Installation

```bash
python -c "from ultralytics import YOLO; print('YOLO Installed Successfully!')"
```

### 3. Run the System

The system has two modes: the **Web Control Center** (FastAPI + React SPA) and the **Standalone CLI Pipeline** (OpenCV GUI).

#### Option A — Web Control Center (React SPA + FastAPI Backend)

**Step 1: Start the FastAPI Backend** (from the project root)

```bash
python -m uvicorn web.app:app --reload --port 8000
```

The REST API and WebSocket telemetry server will be available at:
- REST API: `http://localhost:8000/api/v1/`
- WebSocket: `ws://localhost:8000/ws/telemetry`
- API Docs: `http://localhost:8000/docs`

**Step 2: Install Frontend Dependencies** (first time only)

```bash
cd web-ui
npm install
```

**Step 3: Start the React Dev Server**

```bash
cd web-ui
npm run dev
```

The React Control Center will open at `http://localhost:5173`

> **Note**: The Vite dev server automatically proxies `/api/v1/*` and `/ws/*` to the FastAPI backend on port 8000.

---

#### Option B — Standalone CLI Pipeline (OpenCV GUI)

```bash
python main.py
```

> **Note**: If `videos/traffic.mp4` is not present, `main.py` automatically generates a synthetic traffic video so the pipeline runs immediately out of the box!

---


## 🎯 Key Features

- **YOLO11 Vision Model**: Defaulting to state-of-the-art `yolo11n.pt` for ultra-fast, lightweight inference.
- **Targeted Class Filtering**: Specifically filters for COCO vehicle classes:
  - 🚗 `Car` (ID: 2)
  - 🏍️ `Motorcycle` (ID: 3)
  - 🚌 `Bus` (ID: 5)
  - 🚛 `Truck` (ID: 7)
- **Decoupled Architecture**: Vision inference (`VehicleDetector`) is strictly separated from UI rendering (`Visualizer`).
- **Structured Data Contract**: Returns immutable `Detection` dataclasses with `frame_number`, `timestamp`, and optional `track_id`.
- **Live Performance HUD**: Displays real-time **FPS** and **Inference Latency (ms)**.
- **Timestamped Outputs**: Automatically exports annotated video files to `outputs/detection_YYYYMMDD_HHMMSS.mp4`.
- **Multi-File Logging**: Structured logs stored in `logs/application.log` and `logs/errors.log`.

---

## ⌨️ Controls

- Press **`q`** in the OpenCV display window to exit cleanly.
