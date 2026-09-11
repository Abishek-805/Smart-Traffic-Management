# Smart Traffic Management System

An intelligent, multi-approach traffic intersection management platform powered by real-time computer vision (YOLOv8) and multi-object tracking (ByteTrack). The system ingests live video streams from edge camera nodes, calculates approach vehicle density and queue wait times, and dynamically adapts traffic signal phases to optimize flow and minimize congestion.

> [!IMPORTANT]
> **Companion Mobile Camera Node**:
> Physical edge camera nodes run the dedicated Android client available at:
> **[Traffic_Camera_App Repository](https://github.com/Abishek-805/Traffic_Camera_App)**.
> This repository contains the central Backend server, computer vision inference coordinator, and the React-based Web Management Dashboard.

---

## Overview

The Smart Traffic Management System replaces fixed-timer intersection lights with adaptive, data-driven signal control. Using real-time computer vision, it observes traffic on all four approaches of an intersection (`North`, `South`, `East`, and `West`). The backend calculates vehicle queue lengths, waiting times, and Passenger Car Equivalent (PCE) weighted densities, rotating the green light in a fair clockwise schedule while allocating dynamic green extensions where demand is highest.

### Key Capabilities
- **Real-Time Edge Vision**: YOLOv8 neural network pre-warmed for batched inference across all 4 cameras simultaneously.
- **Occlusion-Resistant Tracking**: Independent ByteTrack instances per approach to track vehicle continuity across momentary occlusions.
- **Fair Adaptive Scheduler**: Real-time phase allocation balancing traffic demand against starvation prevention.
- **Dual Hardware Mode**: Full in-memory simulation mode (no hardware required) or physical ESP32 UART microcontroller output with safe all-red fallback.
- **Real-Time SCADA Dashboard**: High-performance React management dashboard displaying live camera previews, phase timers, lane telemetry, and diagnostic logs.

---

## Architecture

```
+-----------------------------------------------------------------------------------+
|                            EDGE CAMERA SOURCES                                    |
|   Physical Android Nodes (Traffic Camera App) OR Local Video Test Fixtures        |
+-----------------------------------------------------------------------------------+
                                         |
                                         | LAN WebSocket / WebRTC Stream
                                         v
+-----------------------------------------------------------------------------------+
|                        FASTAPI BACKEND & RUNTIME COORDINATOR                      |
|                                                                                   |
|  +------------------------+   +-----------------------+   +--------------------+  |
|  | Frame Coordinator      |-->| Batched YOLOv8        |-->| Per-Approach       |  |
|  | (Backpressure / Auth)  |   | Inference Engine      |   | ByteTrack Tracker  |  |
|  +------------------------+   +-----------------------+   +--------------------+  |
|                                                                     |             |
|                                                                     v             |
|  +------------------------+   +-----------------------+   +--------------------+  |
|  | Telemetry WebSocket &  |<--| Adaptive Phase        |<--| Vehicle Density /  |  |
|  | REST Control API       |   | Fair Scheduler        |   | Queue Estimation   |  |
|  +------------------------+   +-----------------------+   +--------------------+  |
|               |                                                     |             |
+---------------|-----------------------------------------------------|-------------+
                |                                                     |
                v                                                     v
+-------------------------------+                     +-----------------------------+
|    REACT WEB DASHBOARD        |                     |     TRAFFIC CONTROLLER      |
|  (Live feeds, metrics,        |                     |  Simulation Mode (internal) |
|   controls, QR pairing)       |                     |  OR Physical ESP32 (UART)   |
+-------------------------------+                     +-----------------------------+
```

### Deployment Topologies:
1. **Combined Server (Default & Recommended)**: Single FastAPI process hosting REST endpoints, WebSocket camera ingestion, telemetry broadcasts, and compiled static Web UI assets on port `8000`.
2. **Split Microservices (Docker Compose)**: Multi-service containerized deployment separating the REST API (`8000`), WebSocket ingest worker (`8001`), Vite frontend (`5173`), and Redis message broker (`6379`).

---

## Repository Structure

```
smart-traffic-management/
├── ai/
│   ├── camera/            # Stream config and capture adapters
│   ├── controller/        # Signal control managers
│   ├── detection/         # YOLO detector and bounding box types
│   ├── hardware/          # ESP32 serial UART driver and simulation engine
│   ├── models/            # ModelManager, warmup logic, and weight loading
│   ├── pipeline/          # End-to-end traffic perception pipeline
│   ├── signal/            # Priority calculator and adaptive phase scheduler
│   ├── state/             # VehicleStateManager and lane count tracking
│   ├── tracking/          # ByteTrack multi-object tracker
│   └── utils/             # Operational logger and image encoding helpers
├── app-backend/           # Standalone backend service definition for split Docker mode
├── config/                # Centralized settings (deployment profiles, models, paths)
│   ├── deployment.py      # Authoritative runtime profiles (laptop vs. raspberry_pi)
│   ├── model.py           # YOLO and ByteTrack inference parameters
│   └── paths.py           # Filesystem paths
├── core/                  # Application context and runtime lifecycle
├── server/                # Ingestion coordinator, WebSockets, and WebRTC streaming
│   ├── frame_coordinator.py # Directional slot manager and socket auth
│   ├── local_sources.py     # Local video file and synthetic frame fixtures
│   ├── message_handler.py   # WebSocket protocol message dispatcher
│   ├── runtime.py           # Combined background runtime runner
│   ├── webrtc_ingest.py     # aiortc video ingestion worker
│   └── websocket_server.py  # WebSocket endpoints
├── tests/                 # Automated pytest test suites
├── web/                   # FastAPI application, REST endpoints, and schemas
│   ├── routes/            # REST API and dashboard routers
│   ├── services/          # Camera, node, system, and QR pairing services
│   └── app.py             # FastAPI combined application instance
├── web-ui/                # React frontend application (Vite, TypeScript, Tailwind)
├── websocket-server/      # Standalone WebSocket ingest service for Docker mode
├── .env.example           # Template environment configuration
├── docker-compose.yml     # Multi-service container specification
├── requirements.txt       # Core runtime Python dependencies
├── requirements-dev.txt   # Development and test dependencies
├── requirements-laptop.txt# Optional ONNX Runtime acceleration packages
├── run.py                 # Combined server entry point
├── start.ps1              # Automated PowerShell bootstrap and launcher
└── yolov8n.pt             # Default YOLOv8 Nano weights (PyTorch)
```

---

## Prerequisites

Ensure the following runtimes and tools are installed before setting up a fresh machine:

| Tool | Recommended Version | Scope | Purpose |
|---|---|---|---|
| **Python** | `3.12.x` | Runtime / Build | Backend runtime (Python 3.14 lacks pre-built wheels for `lap`/`torch`) |
| **Node.js** | `20.x` or `22.x` (LTS) | Build-time | Required to build frontend Web UI |
| **npm** | `10.x+` | Build-time | Web UI package manager |
| **Git** | Latest | Build-time | Source control |
| *(Optional)* **Docker & Compose** | Docker Desktop 4+ | Runtime | Required only for containerized split deployment |
| *(Optional)* **ESP32 & Micro-USB** | ESP32 Dev Module | Runtime | Required only for physical hardware traffic control |

---

## Fresh Machine Setup

### Automated Launch on Windows (PowerShell)

On a freshly cloned machine, run the automated bootstrap script:

```powershell
git clone https://github.com/Abishek-805/Smart-Traffic-Management.git
cd Smart-Traffic-Management
.\start.ps1 -Lan
```

**What `start.ps1` executes automatically:**
1. Checks for an existing virtual environment in `.venv`; creates one using Python 3.12 if missing.
2. Installs all required runtime and development Python packages (`requirements-dev.txt`).
3. Enters `web-ui`, installs npm packages (`npm ci`), and builds production assets (`npm run build`).
4. Launches the combined server bound to `0.0.0.0:8000` with simulation traffic lights.

Open your browser to: **`http://localhost:8000`** (or `http://<YOUR_LAN_IP>:8000`).

---

## Python Setup

For manual configuration across Windows, Linux, or macOS:

### 1. Create and Activate Virtual Environment
**Windows (PowerShell):**
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS (Bash):**
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements-dev.txt
```
*(Optional: For ONNX Runtime acceleration on laptop profile, run `pip install -r requirements-laptop.txt`)*

---

## Node/Web UI Setup

To compile the React frontend dashboard:

```bash
cd web-ui
npm ci
npm run build
cd ..
```

The production assets are generated in `web-ui/dist`. When running the combined server (`run.py`), FastAPI automatically serves `web-ui/dist/index.html` and mounts static assets at `/assets`.

---

## Redis Setup

- **Combined Server Mode (`run.py`)**: Redis is **not required**. All frame queues, track states, and signal timelines are maintained in-process with zero external dependencies.
- **Split Docker Mode**: Redis 7 runs on port `6379` (`REDIS_URL=redis://localhost:6379`). It acts as a pub/sub message broker and caching layer coordinating frame snapshots and telemetry between the REST and WebSocket workers.

---

## Model Setup

- **Default Model**: `yolov8n.pt` (YOLOv8 Nano, PyTorch, 6.5 MB) is tracked in the repository root.
- **Weight Resolution**: `ai/models/model_manager.py` checks `./yolov8n.pt` first, followed by `models/yolov8n.pt`. If absent, Ultralytics YOLO automatically downloads official weights from GitHub releases.
- **Model Warmup**: During server startup, `ModelManager` feeds synthetic empty tensors matching `YOLO_BATCH_SIZE` (`4` on laptop profile) through the model to compile kernels and eliminate latency spikes on early incoming camera frames.
- **Edge Deployment (Raspberry Pi)**: For ARM devices, NCNN-exported models can be loaded by setting `YOLO_MODEL_NAME=models/yolo26n_ncnn_model` (see `docs/RASPBERRY_PI_DEPLOYMENT.md`).

---

## Environment Variables

Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```

| Variable | Purpose | Default | Scope |
|---|---|---|---|
| `CAMERA_PUBLIC_HOST` | Host IP advertised in camera QR codes | Auto-detected LAN IP | Server |
| `CAMERA_WS_PORT` | Port for camera WebSocket connections | `8000` (`8001` in Docker) | Server |
| `CAMERA_WS_SECURE` | Enable secure WebSocket (`wss://`) | `false` | Server |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` | Docker / Split |
| `TRAFFIC_PROFILE` | Performance target (`laptop` or `raspberry_pi`) | `laptop` | Core |
| `HARDWARE` | Signal mode (`simulation` or `esp32`) | `simulation` | Hardware |
| `ESP32_PORT` | Serial port (e.g. `COM3` or `/dev/ttyUSB0`) | None (required if esp32) | Hardware |
| `ESP32_BAUDRATE` | Serial baudrate | `115200` | Hardware |
| `YOLO_MODEL_NAME` | YOLO weights file | `yolov8n.pt` | Vision |
| `YOLO_INPUT_SIZE` | Model input dimensions | `576` (laptop) / `512` (Pi) | Vision |
| `YOLO_CONFIDENCE_THRESHOLD` | Detection confidence floor | `0.08` | Vision |
| `YOLO_IOU` | Non-maximum suppression IoU threshold | `0.60` | Vision |
| `YOLO_MAX_DETECTIONS` | Max bounding boxes per frame | `300` | Vision |
| `YOLO_CPU_THREADS` | Inference CPU thread count | `4` | Vision |
| `YOLO_BATCH_SIZE` | Batched frames per model forward pass | `4` (laptop) / `1` (Pi) | Vision |
| `YOLO_DEVICE` | Execution device (`auto`, `cpu`, `cuda`) | `auto` | Vision |
| `TRACK_HIGH_THRESHOLD` | ByteTrack track initiation threshold | `0.15` | Tracking |
| `TRACK_LOW_THRESHOLD` | ByteTrack track continuation threshold | `0.08` | Tracking |
| `TRACK_MATCH_THRESHOLD` | ByteTrack IoU matching threshold | `0.80` | Tracking |
| `TRACK_BUFFER_FRAMES` | Frames to hold track through occlusion | `12` | Tracking |
| `TRAFFIC_NORTH_SOURCE` | Optional local video fixture for North | None | Testing |

---

## Backend Startup

To start the combined server manually:

```powershell
.\.venv\Scripts\python.exe run.py --host 0.0.0.0 --port 8000
```
*(On Linux/macOS: `python run.py --host 0.0.0.0 --port 8000`)*

Arguments:
- `--host`: Bind address (use `0.0.0.0` for LAN access, `127.0.0.1` for local-only).
- `--port`: Port number (default `8000`).

---

## WebSocket/AI Startup

In the combined deployment (`run.py`), the inference engine, camera coordinator, and WebSocket listeners start automatically within the FastAPI lifespan context.

In the optional split Docker architecture, the WebSocket server can be run independently:
```powershell
cd websocket-server
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

---

## Web UI Startup

- **Production Mode (Built Assets)**: Served automatically at `http://localhost:8000` by the combined server after running `npm run build`.
- **Development Mode (Hot Reloading)**:
  ```powershell
  cd web-ui
  npm run dev
  ```
  Launches the Vite dev server on `http://localhost:5173`, proxying API calls to `http://localhost:8000`.

---

## Docker Setup

To run the full multi-service microservice stack using Docker Compose:

```powershell
# Set host LAN IP for mobile camera QR codes
$env:CAMERA_PUBLIC_HOST = "192.168.1.100"

# Build and start containers
docker compose up --build
```

**Port Allocations in Docker:**
- `app-backend`: Port `8000` (REST API)
- `websocket-server`: Port `8001` (Camera Ingestion & Telemetry)
- `web-ui`: Port `5173` (Frontend Dashboard)
- `redis`: Port `6379` (In-memory message broker)

---

## Mobile Integration

Edge camera phones run the companion **[Traffic Camera App](https://github.com/Abishek-805/Traffic_Camera_App)**.

1. Connect both PC and phones to the same Wi-Fi router.
2. Open `http://<YOUR_LAN_IP>:8000` in your computer's browser.
3. Go to **Live Cameras** -> **Pair Camera Node**.
4. Select an approach (`North`, `South`, `East`, `West`).
5. Click **Generate QR Code**.
6. Scan the QR code using the mobile app to establish an authenticated WebSocket session on `/ws/camera`.

---

## Multi-Camera Setup

- **Intersection Approaches**: The system tracks 4 approaches independently: `NORTH`, `SOUTH`, `EAST`, and `WEST`.
- **Batched Inference**: The coordinator gathers the latest available frame from each active camera and executes inference in a single batched tensor pass (`batch_size=4`), maximizing CPU throughput.
- **Offline Video Testing**: To test multi-camera functionality without physical phones, configure local video files:
  ```powershell
  $env:TRAFFIC_NORTH_SOURCE = "videos/north.mp4"
  $env:TRAFFIC_SOUTH_SOURCE = "videos/south.mp4"
  $env:TRAFFIC_EAST_SOURCE  = "videos/east.mp4"
  $env:TRAFFIC_WEST_SOURCE  = "videos/west.mp4"
  python run.py --host 0.0.0.0 --port 8000
  ```

---

## ESP32 / Simulation

### Simulation Mode (Default)
Runs in software without external hardware. Signal phases and countdown timers are computed in-memory and rendered on the web dashboard.

### Physical ESP32 Hardware Mode
To control physical traffic signal hardware:
```powershell
$env:HARDWARE = 'esp32'
$env:ESP32_PORT = 'COM3'         # Linux: '/dev/ttyUSB0'
$env:ESP32_BAUDRATE = '115200'
python run.py --host 0.0.0.0 --port 8000
```
> [!NOTE]
> If `HARDWARE=esp32` is configured but the serial port cannot be opened, the system safely halts in an **all-red safe state** instead of masking the error.

---

## API Endpoints

FastAPI exposes REST endpoints under `/api/v1`:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/system/health` | System health, active profile, and hardware status |
| `GET` | `/api/v1/system/status` | Current intersection state, active phase, and queue counts |
| `POST`| `/api/v1/system/start` | Start adaptive traffic pipeline |
| `POST`| `/api/v1/system/stop` | Stop traffic pipeline (transitions to all-red) |
| `POST`| `/api/v1/system/config` | Update runtime detection confidence and green times |
| `GET` | `/api/v1/cameras` | Status of all 4 camera slots |
| `GET` | `/api/v1/cameras/{direction}/feed` | Latest annotated JPEG frame for an approach |
| `DELETE` | `/api/v1/cameras/{direction}` | Disconnect and unpair a camera slot |
| `GET` | `/api/v1/qr/generate?direction={dir}` | Generate authenticated QR pairing payload |
| `GET` | `/api/v1/analytics` | Intersection PCE throughput and wait-time statistics |
| `GET` | `/api/v1/logs` | Operational event logs |

---

## WebSocket Endpoints

| Endpoint | Protocol | Purpose |
|---|---|---|
| `/ws/camera` | JSON / Binary | Camera node registration, authentication, WebRTC signaling, and frame ingestion |
| `/ws/telemetry` | JSON Broadcast | Real-time vehicle counts, phase states, and hardware health to Web UI |

---

## Testing

Execute the automated test and verification commands:

```powershell
# 1. Run Python test suite (101 unit/integration tests)
.\.venv\Scripts\python.exe -m pytest -q

# 2. Verify Python bytecode compilation
.\.venv\Scripts\python.exe -m compileall -q ai core config server web

# 3. Web UI static type checking and production build
cd web-ui
npm run lint
npm run build
cd ..
```

---

## Troubleshooting

### Port 8000 is already in use
```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess
Stop-Process -Id <PID> -Force
```

### Python package installation errors (`lap` or `torch`)
Ensure you are using **Python 3.12**. Python 3.14 lacks pre-compiled wheels for scientific packages on Windows.

### Mobile app cannot connect to backend
1. Confirm both laptop and smartphone are on the same Wi-Fi subnet.
2. Verify host IP via `ipconfig` (Windows) or `ip a` (Linux).
3. Allow Python through Windows Defender Firewall for both Private and Public networks.

### Serial port permission denied (ESP32)
Ensure no serial terminal (PuTTY, Arduino IDE Serial Monitor) is holding the COM port open before starting the server.

---

## Known Limitations

1. **Approach Capacity**: Exactly 4 approaches (`NORTH`, `SOUTH`, `EAST`, `WEST`) are supported per intersection instance.
2. **Local Area Network**: Built for trusted LAN environments using cleartext HTTP and WebSocket protocols.
3. **Emergency Vehicles**: Prioritization logic requires fine-tuning on domain-specific emergency vehicle datasets.
