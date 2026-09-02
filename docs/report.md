# Executive & Technical Report: Smart Traffic Management System

---

## 1. Executive Summary

The **Smart Traffic Management System** is a next-generation, AI-driven adaptive traffic signal control solution designed to optimize urban intersection throughput. 

The system leverages state-of-the-art computer vision (**YOLO11 + ByteTrack**) to measure approach vehicle densities in real-time, computes dynamic Passenger Car Equivalent (**PCE**) queue metrics, and optimizes signal phase timing.

The architecture was matured into a modern **3-tier enterprise web platform** consisting of a **React 18 SPA frontend**, a **FastAPI backend transport layer**, and a **frozen AI perception core**, alongside a **React Native (Expo) mobile camera node app**.

---

## 2. System Architecture & Components

```
                ┌──────────────────────────────────────────────┐
                │          React SPA (Vite + TS)               │
                │        http://localhost:5173                │
                └──────────────────────┬───────────────────────┘
                                       │ REST API (/api/v1/*)
                                       │ WebSocket (/ws/telemetry)
                                       ▼
                ┌──────────────────────────────────────────────┐
                │             FastAPI Web Server               │
                │          http://localhost:8000               │
                └──────────────────────┬───────────────────────┘
                                       │ ApplicationContext
                                       ▼
  ┌───────────────────────────┬───────────────────────────┬───────────────────────────┐
  │   Session / Connection    │   Multi-Camera Stream     │   AI Perception Engine    │
  │        Managers           │         Service           │  YOLO11 → ByteTrack → PCE │
  └─────────────▲─────────────┴─────────────▲─────────────┴───────────────────────────┘
                │                           │
         WebSocket (/ws/camera)       MJPEG Stream
                │                           │
  ┌─────────────┴─────────────┐    ┌────────┴──────────────┐
  │  Mobile Camera App (Expo) │    │  Live Stream Preview  │
  └───────────────────────────┘    └───────────────────────┘
```

### Key Architectural Pillars:
1. **Presentation Layer (`web-ui`)**: React 18, Vite, TypeScript, React Query, Lucide Icons, Recharts.
2. **Transport & API Layer (`web/`)**: FastAPI, Pydantic schemas, standard response envelopes (`{ "success": true, ... }`), 308 Permanent Redirects for legacy endpoints.
3. **Communication Engine (`server/`)**: Strongly typed WebSocket protocol, protocol versioning (`1.0`), correlation ID echoing, dynamic QR pairing.
4. **AI Perception Core (`ai/` & `core/`)**: Object detection, multi-object tracking, dynamic queue length calculation, adaptive phase scheduling.

---

## 3. Work Completed & Features Implemented

### A. Frontend Control Center (`web-ui`)
- **Dashboard & System Overview**:
  - Live signal phase indicators (North, East, South, West).
  - Real-time PCE queue score metrics and vehicle counts.
  - Interactive WebSocket live telemetry charts powered by Recharts.
- **Intersection Devices & Hardware Management**:
  - **Dynamic Multi-Direction QR Pairing Wizard**: Allows pairing mobile nodes to specific approach slots (`North`, `South`, `East`, `West`).
  - **Live Stream Preview Modal**: Allows real-time preview of any approach stream feed via high-frequency MJPEG streaming.
  - **Mobile Node Monitoring**: Displays connected smartphone node status, FPS, latency, battery levels, and signal quality.
  - **ESP32 Hardware Panel**: Dedicated interface status display for hardware signal controllers.
- **Analytics & Operational Insights**:
  - Vehicle classification distribution (Car, Motorcycle, Bus/Heavy, Emergency).
  - Hourly traffic flow trends and approach efficiency metrics.
- **System Logs & Configuration**:
  - Structured, filterable log system with level and component filters.

### B. FastAPI Web Backend (`web/`)
- **Standardized REST API v1**:
  - `/api/v1/system/health`, `/api/v1/system/status`, `/api/v1/system/start`, `/api/v1/system/stop`.
  - `/api/v1/cameras`, `/api/v1/cameras/{direction}/feed` (MJPEG stream).
  - `/api/v1/mobile-nodes`, `/api/v1/qr/generate?direction={direction}`.
  - `/api/v1/analytics`, `/api/v1/logs`.
- **Legacy Route Redirection**: Automatic HTTP 308 Permanent Redirect from `/api/*` to canonical `/api/v1/*`.
- **Application Context Integration**: Thread-safe singleton (`ApplicationContext`) holding frame buffers, active sessions, and AI state.

### C. WebSocket Server & Protocol (`server/`)
- **Protocol Version Validation**: Enforces matching `protocol_version` (`1.0`) and emits structured `PROTOCOL_VERSION_MISMATCH` errors when incompatible.
- **ACK Request Correlation**: Echoes incoming message `id` in `REGISTRATION_ACK` and `HEARTBEAT_ACK` responses to eliminate client state hangs.
- **Directional QR Code Payloads**: Customizes pairing payloads (`CAM-NORTH-PAIR`, `CAM-SOUTH-PAIR`, etc.) and lane labels according to targeted approach direction.
- **Live Frame Ingestion**: Handles `VIDEO_FRAME` payloads over WebSocket and updates `ApplicationContext.frame_buffer`.

### D. Mobile Camera Companion App (`traffic-camera-app`)
- **Python Dict Preprocessing**: `QRCodeService.ts` normalizes Python dict string representations (single quotes, `True`/`False`/`None`) to standard JSON.
- **Resilient Protocol Validator**: Tolerates optional message correlation IDs while maintaining strong message schema validation.

---

## 4. Run & Deployment Guide

### Mode 1 — Enterprise Web Control Center (React SPA + FastAPI)

**Terminal 1 — FastAPI Backend**:
```bash
python -m uvicorn web.app:app --reload --port 8000
```
- REST API: `http://localhost:8000/api/v1/`
- WebSocket Telemetry: `ws://localhost:8000/ws/telemetry`
- Swagger OpenAPI Docs: `http://localhost:8000/docs`

**Terminal 2 — React Control Center SPA**:
```bash
cd web-ui
npm install   # First time only
npm run dev
```
- React SPA: `http://localhost:5173`

**Terminal 3 — Smartphone Camera Companion App**:
```bash
cd traffic-camera-app
npx expo start
```

---

### Mode 2 — Standalone CLI AI Perception Pipeline

```bash
python main.py
```
- Launches the standalone OpenCV dashboard only with explicitly configured real USB, RTSP, or video sources; there is no synthetic fallback.

---

## 5. Verification & Build Validation

| Component | Test / Command | Result |
| :--- | :--- | :--- |
| **Python Backend Core** | `python -m py_compile server/protocol.py server/message_handler.py web/app.py web/routes/api_routes.py web/services/node_service.py web/services/camera_service.py` | **PASSED (0 errors)** |
| **React SPA Frontend** | `tsc && vite build` | **PASSED (Production bundle created cleanly)** |

---

## 6. Summary of Key Achievements

1. Built a **production-ready 3-tier system** with complete frontend/backend separation.
2. Solved mobile camera QR pairing, ACK hangs, and Python dict format compatibility.
3. Enabled **multi-direction targeted pairing** (North, South, East, West) and live MJPEG stream preview modal.
4. Preserved the frozen AI perception core while creating clean FastAPI & WebSocket transport layers.
