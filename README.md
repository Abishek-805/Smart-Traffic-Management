# Smart Traffic Management System

An enterprise-grade, real-time AI traffic management system powered by **YOLO11**, **ByteTrack**, **FastAPI**, **Redis**, and **React SCADA UI**.

---

## 1. Overview

The **Smart Traffic Management System** is a distributed, real-time computer vision and signal control system designed to optimize urban traffic intersection flow. Mobile edge devices (smartphones running the `traffic-camera-app`) act as wireless traffic sensors, streaming high-frame-rate video feeds to a centralized perception server. The backend runs YOLO11 vehicle detection and ByteTrack object tracking to compute live Passenger Car Equivalent (PCE) queue metrics, dynamic green phase timing, and emergency vehicle priority overrides.

---

## 2. Architecture

```
                                  +---------------------------------------+
                                  |     Mobile Camera App (Android)       |
                                  |   (Independent App Repository)       |
                                  +---------------------------------------+
                                                      |
                                                      | WebSocket (/ws/camera)
                                                      v
                                  +---------------------------------------+
                                  | WebSocket Server & Perception Engine  |
                                  |        (FastAPI - Port 8001)          |
                                  |       - YOLO11 Vehicle Detector       |
                                  |       - ByteTrack Multi-Object Tracker|
                                  |       - PCE Queue Density Engine      |
                                  +---------------------------------------+
                                                      |
                                                      | Redis Pub/Sub Event Bus
                                                      v
                                  +---------------------------------------+
                                  |          App REST Backend             |
                                  |        (FastAPI - Port 8000)          |
                                  |       - System & Node Management      |
                                  |       - Analytics & Log Storage       |
                                  |       - QR Code Pairing Generator     |
                                  +---------------------------------------+
                                                      |
                                                      | HTTP REST & WebSocket (/ws/telemetry)
                                                      v
                                  +---------------------------------------+
                                  |        React + Vite SCADA UI          |
                                  |          (Port 5173 / Web)            |
                                  +---------------------------------------+
```

---

## 3. Requirements

- **Operating System**: Windows 10/11, Linux (Ubuntu 20.04+), or macOS (12+)
- **Python**: Version `3.10` or higher (tested with Python 3.12/3.14)
- **Node.js**: Version `18.x` or higher
- **npm**: Version `9.x` or higher
- **Docker Desktop** *(Optional)*: If running system via containers
- **Redis Server** *(Optional)*: Required when running without Docker (`redis-server`)

---

## 4. Clone Repository

```bash
git clone https://github.com/Abishek-805/Smart-Traffic-Management.git
cd Smart-Traffic-Management
```

---

## 5. Python Virtual Environment

### Windows (PowerShell / Command Prompt)

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Linux / macOS (Bash / Zsh)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 6. Development Dependencies

For running unit tests, end-to-end simulation suites, and test runners:

```bash
pip install -r requirements-dev.txt
```

---

## 7. Environment Configuration

Copy `.env.example` to create your local `.env` configuration file:

### Windows (PowerShell)
```powershell
Copy-Item .env.example .env
```

### Linux / macOS
```bash
cp .env.example .env
```

### Key Environment Variables

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `PORT` | `8000` | Port for REST App Backend |
| `WEBSOCKET_SERVER_PORT` | `8001` | Port for WebSocket & AI Server |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL for Pub/Sub event bus |
| `HOST` | `0.0.0.0` | Bind host for server processes |
| `DEBUG` | `true` | Enable detailed debug logs |
| `VITE_API_BASE` | `http://localhost:8000/api/v1` | SCADA UI target REST API URL |
| `VITE_WS_URL` | `ws://localhost:8001/ws/telemetry` | SCADA UI target telemetry WebSocket |
| `VITE_CAMERA_WS_URL` | `ws://localhost:8001/ws/camera` | Mobile camera streaming WebSocket |

---

## 8. Web UI Installation

```bash
cd web-ui
npm ci
cd ..
```

---

## 9. Run with Docker

To build and launch the complete stack (Redis, REST Backend, WebSocket AI Server, and Web UI SCADA Frontend) in Docker:

```bash
docker compose up --build
```

### Docker Services & Port Mappings

- **Redis Server**: `localhost:6379`
- **App Backend (REST API)**: `http://localhost:8000` (Docs: `http://localhost:8000/docs`)
- **WebSocket / AI Server**: `ws://localhost:8001` (Docs: `http://localhost:8001/docs`)
- **Web UI SCADA Dashboard**: `http://localhost:5173`

To stop all services:
```bash
docker compose down
```

---

## 10. Run Without Docker

If running locally on your host machine, start each service in a separate terminal window:

### Terminal 1: Redis Server
*(Skip if Redis service is already running on port 6379)*
```bash
redis-server
```

### Terminal 2: App Backend (Port 8000)
```bash
cd app-backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 3: WebSocket + AI Perception Server (Port 8001)
```bash
cd websocket-server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```


### Terminal 4: Web UI SCADA Frontend
```bash
cd web-ui
npm run dev
```

---

## 11. API Endpoints

The App Backend provides OpenAPI/Swagger documentation at `http://localhost:8000/docs`.

### Core REST Endpoints (`/api/v1`)

- `GET /api/v1/system/health`: System health metrics (CPU, RAM, latency, status)
- `GET /api/v1/system/status`: Intersection operational status & signal phase info
- `POST /api/v1/system/start`: Start AI perception engine processing loop
- `POST /api/v1/system/stop`: Pause AI perception engine processing loop
- `GET /api/v1/cameras`: Query active camera configuration and feeds
- `GET /api/v1/mobile-nodes`: List connected edge camera nodes and metrics
- `GET /api/v1/analytics`: Query vehicle flow totals, PCE queue trends, and phase efficiency
- `GET /api/v1/logs`: System logs with category, level, and keyword filtering
- `GET /api/v1/qr/generate?direction=north`: Generate QR code pairing payload and Base64 image for mobile pairing

---

## 12. WebSocket Endpoints

The WebSocket Server operates on **Port 8001**:

### 1. Camera Video Streaming Endpoint
- **URL**: `ws://<SERVER_IP>:8001/ws/camera`
- **Protocol Flow**:
  1. **REGISTER_CAMERA** (Mobile → Server): Mobile client connects and sends JSON registration payload containing `node_id`, `camera_direction` (`north`, `south`, `east`, `west`), `resolution`, `fps`, and device details.
  2. **REGISTRATION_ACK** (Server → Mobile): Server acknowledges registration with status `CONNECTED` and returns `session_token`.
  3. **START_STREAM** (Server → Mobile): Server sends `START_STREAM` signal instructing mobile device to start capturing and sending frames.
  4. **VIDEO_FRAME** (Mobile → Server): Mobile client streams structured JSON `VIDEO_FRAME` messages containing `frame_id`, approach `direction`, Base64-encoded JPEG image string in `payload.frame_data`, `capture_timestamp`, and `upload_timestamp`.

### 2. SCADA Telemetry Stream Endpoint
- **URL**: `ws://<SERVER_IP>:8001/ws/telemetry`
- **Description**: Streams live JSON `SystemStatusUpdated` telemetry snapshots (PCE queue metrics, signal phase states, bounding boxes, system health) to connected SCADA dashboards at 30 FPS.


---

## 13. Mobile Camera Connection

The mobile Android application (`traffic-camera-app`) is an **independent separate repository** and mobile client. It connects to this backend via WebSockets.

### Connecting a Mobile Device:

1. Connect your Android device to the same Wi-Fi / Local Area Network as your server laptop.
2. Determine your laptop's local IP address (`ipconfig` on Windows or `ifconfig` / `ip a` on Linux/macOS). Example: `192.168.1.100`.
3. Open the `traffic-camera-app` on the phone.
4. Scan the QR code generated by the Web UI (`http://localhost:5173/settings` or via `http://localhost:8000/api/v1/qr/generate?direction=NORTH`) or manually input the WebSocket URL:
   ```
   ws://192.168.1.100:8001/ws/camera
   ```
5. Assign a distinct approach direction to each phone:
   - Phone 1: `NORTH`
   - Phone 2: `SOUTH`
   - Phone 3: `EAST`
   - Phone 4: `WEST`

---

## 14. Multi-Camera Architecture

- **Independent WebSocket Sockets**: Each mobile node opens a dedicated WebSocket connection on `/ws/camera`.
- **Directional Isolation**: Frame processors run in isolated queues indexed by approach direction (`NORTH`, `SOUTH`, `EAST`, `WEST`).
- **ByteTrack Multi-Object Tracking**: Vehicle trajectories and track IDs are calculated per approach feed independently, ensuring no track ID collision occurs across approaches.
- **Aggregated PCE Queue Computation**: The Signal Scheduler combines vehicle counts, vehicle classes (cars, buses, emergency vehicles), and approach wait times to calculate dynamic green phase allocations.

---

## 15. Testing & Build Verification

### Backend Pytest Suite
Run all unit and integration tests from the repository root:

```bash
python -m pytest
```

*Expected output: All 41 tests pass.*

### Frontend Production Build
Verify that the React SCADA frontend compiles cleanly:

```bash
cd web-ui
npm run build
```

---

## 16. Troubleshooting

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Port 8000 or 8001 in use** | Another process is bound to port 8000 or 8001 | Stop conflicting processes (`taskkill /F /IM python.exe` on Windows or `fuser -k 8000/tcp` on Linux). |
| **Redis connection refused** | Redis server is not running locally | Ensure Redis container is up (`docker compose up redis -d`) or start `redis-server` locally. |
| **Python `ModuleNotFoundError`** | Package not installed or virtual environment unactivated | Activate virtual environment (`source .venv/bin/activate` or `.\.venv\Scripts\activate`) and run `pip install -r requirements.txt`. |
| **Phone cannot connect to WebSocket** | Windows Firewall blocking port 8001 or incorrect IP | Allow Python / Port 8001 in Windows Defender Firewall rules and verify phone and laptop are on the same Wi-Fi subnet. |
| **YOLO model missing** | `yolo11n.pt` not found in root or `models/` | Ultralytics automatically downloads `yolo11n.pt` on initial launch when connected to the internet. |
| **`npm.ps1` execution error on Windows** | PowerShell Execution Policy restricts script execution | Run `cmd /c npm ci` or set execution policy via `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`. |

---

## License

Distributed under the MIT License. See `LICENSE` for details.
