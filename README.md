# Smart Traffic Management System

An intelligent, multi-approach traffic intersection management platform powered by real-time computer vision (YOLOv8) and multi-object tracking (ByteTrack). The system ingests live video streams from edge camera nodes, calculates approach vehicle density and queue wait times, and dynamically adapts traffic signal phases to optimize flow and minimize congestion.

> [!IMPORTANT]
> **Companion Mobile Camera Node**:
> Physical edge camera nodes run the dedicated Android client available at:
> **[Traffic_Camera_App Repository](https://github.com/Abishek-805/Traffic_Camera_App)**.
> This repository contains the central Backend server, computer vision inference coordinator, and the React-based Web Management Dashboard.

---

## System Architecture

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

### Execution Topologies

The system supports two deployment topologies:

1. **Combined Server (Default & Recommended for Local/Laptop Testing)**:
   - Single FastAPI process hosting the REST API, Camera WebSocket coordinator, Telemetry WebSocket, and pre-compiled static Web UI on port **8000**.
   - Zero external service dependencies (no Redis required).
2. **Split Microservices (Docker Compose)**:
   - Containerized multi-service deployment with Redis pub/sub (`6379`), REST backend (`8000`), dedicated high-throughput WebSocket ingestion server (`8001`), and Vite UI dev server (`5173`).

---

## Prerequisites

Ensure the following runtimes and tools are installed before setting up a fresh machine:

| Tool | Recommended Version | Notes |
|---|---|---|
| **Python** | `3.12.x` | Required. (Python 3.14 is currently incompatible with PyTorch/lap binary wheels). |
| **Node.js** | `20.x` or `22.x` (LTS) | Required to build the frontend Web UI. |
| **npm** | `10.x+` | Package manager for Web UI. |
| **Git** | Latest | Source control. |
| *(Optional)* **Docker & Compose** | Docker Desktop 4+ | Required only if running the containerized split deployment. |
| *(Optional)* **ESP32 & Micro-USB** | ESP32 Dev Module | Required only when running in physical hardware mode (`HARDWARE=esp32`). |

---

## Fresh Machine Quickstart

### Automated Launch on Windows (PowerShell)

On a freshly cloned machine, run the automated setup and launch script from PowerShell:

```powershell
.\start.ps1 -Lan
```

**What this script does automatically:**
1. Verifies or creates a clean Python 3.12 virtual environment in `.venv`.
2. Installs all required runtime and development Python packages (`requirements-dev.txt`).
3. Enters `web-ui`, installs npm packages via `npm ci`, and compiles production assets (`npm run build`).
4. Launches the combined FastAPI server bound to `0.0.0.0:8000` with simulation traffic lights.

Open your browser to: **`http://localhost:8000`** (or `http://<YOUR_LAN_IP>:8000`).

#### Useful `start.ps1` Flags:
- `.\start.ps1 -Lan` — Binds to `0.0.0.0` so mobile phones on the same Wi-Fi network can connect.
- `.\start.ps1 -Lan -SkipInstall` — Skips pip/npm dependency checks on subsequent launches for instant startup.
- `.\start.ps1 -Lan -PythonPath 'C:\Python312\python.exe'` — Explicitly points to your Python 3.12 binary if multiple Python versions are installed.

---

## Manual Step-by-Step Setup (Cross-Platform)

For Linux, macOS, or custom Windows environments:

### 1. Clone the Repository
```bash
git clone https://github.com/Abishek-805/Smart-Traffic-Management.git
cd Smart-Traffic-Management
```

### 2. Configure Python Virtual Environment
Create and activate a virtual environment using Python 3.12:

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

### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements-dev.txt
```
*(Optional: for ONNX Runtime acceleration on laptop profile, run `pip install -r requirements-laptop.txt`)*

### 4. Build Frontend Web UI
```bash
cd web-ui
npm ci
npm run build
cd ..
```
The compiled assets are placed in `web-ui/dist`, which FastAPI serves automatically at the root URL.

### 5. Configure Environment Variables
Copy the environment template:
```bash
cp .env.example .env
```
Key configuration options in `.env`:
- `TRAFFIC_PROFILE`: Set to `laptop` (default, multi-core CPU batching) or `raspberry_pi` (resource-constrained SBC).
- `HARDWARE`: Set to `simulation` (default) or `esp32` (physical microcontroller).
- `YOLO_MODEL_NAME`: Set to `yolov8n.pt` (default).

### 6. Start the Combined Server
```bash
python run.py --host 0.0.0.0 --port 8000
```

---

## YOLO Vision Models & Detection

- **Default Model**: `yolov8n.pt` is tracked directly in the repository root. If missing, Ultralytics YOLO automatically downloads standard weights from official releases upon initial startup.
- **Model Warmup**: The inference manager automatically pre-warms the detector at startup with synthetic tensors matching the configured batch size (`4` on laptop profile) to prevent dropped frames on early incoming camera feeds.
- **Supported Detection Classes**: Cars, buses, trucks, motorcycles, and bicycles.
- **Model Storage**: Models can be placed in the project root (`./yolov8n.pt`) or inside the `models/` directory (`models/yolov8n.pt`).
- **Edge Deployment (Raspberry Pi)**: For resource-constrained ARM devices, see [`docs/RASPBERRY_PI_DEPLOYMENT.md`](docs/RASPBERRY_PI_DEPLOYMENT.md) for instructions on running NCNN-exported models.

---

## Hardware Controller vs. Simulation

The system controls traffic signal timings (Red, Yellow, Green) for all 4 intersection approaches (North, South, East, West).

### Simulation Mode (Default)
No external hardware required. The internal signal controller maintains phase transitions, calculates adaptive green times, and exposes signal states through the dashboard and WebSocket telemetry in real time.

### Physical ESP32 Hardware Mode
To connect a physical ESP32 traffic light controller via UART:
1. Flash your ESP32 with compatible firmware listening for serial phase commands.
2. Connect the ESP32 via USB and identify the serial port (e.g., `COM3` on Windows, `/dev/ttyUSB0` on Linux).
3. Start the server with hardware mode enabled:
   ```powershell
   $env:HARDWARE = 'esp32'
   $env:ESP32_PORT = 'COM3'
   $env:ESP32_BAUDRATE = '115200'
   python run.py --host 0.0.0.0 --port 8000
   ```
> [!NOTE]
> If `HARDWARE=esp32` is configured but the serial port cannot be opened, the system safely halts in an **all-red safe state** instead of silently masking hardware failure.

---

## Connecting Mobile Camera Nodes

The server pairs with phones running the **[Traffic Camera Node](https://github.com/Abishek-805/Traffic_Camera_App)**.

1. Connect your computer and mobile phones to the **same local Wi-Fi network**.
2. Open the dashboard at `http://<YOUR_LAPTOP_LAN_IP>:8000`.
3. Navigate to **Live Cameras** -> **Pair Camera Node**.
4. Select the target approach direction (`North`, `South`, `East`, or `West`).
5. Click **Generate QR Code**.
6. In the mobile app, tap **Scan QR** and scan the code on the screen.
7. The phone establishes an authenticated WebSocket session, streaming frames directly to the backend coordinator.

---

## Optional Split Deployment (Docker Compose)

For distributed production testing using Docker:

```powershell
# Set your host LAN IP for the mobile cameras
$env:CAMERA_PUBLIC_HOST = '192.168.1.100'

# Build and start all services
docker compose up --build
```

**Exposed Services:**
- `app-backend`: FastAPI REST API on port `8000`
- `websocket-server`: Camera ingestion & telemetry on port `8001`
- `web-ui`: Vite frontend development server on port `5173`
- `redis`: In-memory state and telemetry pub/sub on port `6379`

---

## Automated Verification & Testing

Verify that your environment and all subsystems are functioning correctly:

```powershell
# 1. Run full Python test suite (78 tests)
.\.venv\Scripts\python.exe -m pytest -q

# 2. Verify Python bytecode compilation across all modules
.\.venv\Scripts\python.exe -m compileall -q ai core config server web

# 3. Test Web UI linting and production build
cd web-ui
npm run lint
npm run build
cd ..

# 4. Validate Docker Compose configuration
docker compose config
```

### Synthetic Runtime Smoke Test
With the backend server running on `http://localhost:8000`, run the automated smoke test script to simulate 4 camera nodes and verify end-to-end telemetry:
```powershell
.\.venv\Scripts\python.exe scripts/smoke_runtime.py
```

---

## Troubleshooting

### Port 8000 is already in use
- Another instance of `run.py` or a background server is already listening on port 8000.
- Check and terminate the process:
  ```powershell
  Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess
  Stop-Process -Id <PID> -Force
  ```

### Mobile app cannot connect to backend
1. Ensure both your computer and phone are connected to the same Wi-Fi router.
2. Check your computer's LAN IP using `ipconfig` (Windows) or `ip a` (Linux).
3. Ensure Windows Defender Firewall allows inbound traffic on port 8000:
   - When Windows prompts "Allow Python through Firewall", allow both Private and Public networks.
4. Verify by navigating to `http://<LAN_IP>:8000` from the mobile phone's browser.

### Python version incompatibility (`lap` or `torch` wheel error)
- If you encounter build errors when installing `lap` or `torch`, verify your Python version with `python --version`.
- Python 3.12 is required. Python 3.14 lacks pre-built wheels for scientific packages on Windows.
