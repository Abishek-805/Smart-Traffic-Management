# Smart Traffic Management System

A local traffic-monitoring prototype: four Android camera nodes send JPEG samples to
a configurable YOLO detector and independent ByteTrack trackers. The laptop test
profile uses YOLO26s; the Raspberry Pi candidate is a fine-tuned YOLO26n NCNN model.
FastAPI serves the dashboard, directional camera previews, measured telemetry and a
simulated adaptive signal controller.

**Use only on a trusted LAN.** Camera registration uses an expiring one-time QR
secret and the server issues a session token for later frames/reconnects. REST
operator controls still have no login and local WebSockets use cleartext by default.
Do not expose these ports to the internet or connect this prototype directly to
public-road signals.

See the [implementation plan](docs/IMPLEMENTATION_PLAN.md),
[optimization measurements](docs/OPTIMIZATION_REPORT.md) and
[validation report](docs/VALIDATION_REPORT.md) for scope and remaining checks.
The [Raspberry Pi deployment guide](docs/RASPBERRY_PI_DEPLOYMENT.md) records the
edge model choice, NCNN setup, and required accuracy gate.

## Start on Windows

Prerequisites: Python 3.12, Node.js 22.12+ with npm, and internet for first installation.
Use the Python environment in this repository rather than a system Python 3.14 install.

From PowerShell in this repository:

```powershell
.\start.ps1 -Lan
```

This creates `.venv`, installs Python dependencies, runs `npm ci` and builds the web
UI, then starts the combined service at **http://localhost:8000**. No Redis, Docker
or demo videos are required. The first install includes PyTorch and can take time.

If Python is not registered with the Windows Python launcher:

```powershell
.\start.ps1 -Lan -PythonPath 'C:\path\to\Python312\python.exe'
```

Subsequent starts can use `.\start.ps1 -Lan -SkipInstall`. Omit `-Lan` for
computer-only access. If PowerShell blocks a downloaded script, review it and use
`powershell -ExecutionPolicy Bypass -File .\start.ps1 -Lan` for this invocation;
there is no need to change the machine's execution policy.

Python-only launch after installation and web build:

```powershell
.\.venv\Scripts\python.exe run.py --host 0.0.0.0 --port 8000
```

## Connect the Android apps

The app source is the sibling `traffic-camera-app` repository. It needs a native
Android build; **Expo Go cannot run the VisionCamera/Nitro streaming implementation**.

1. Put laptop and phones on the same trusted Wi-Fi network.
2. Start with `-Lan`. Allow the Python process through Windows Firewall on your
   private network if Windows asks. Do not disable the firewall.
3. Open **Live Cameras → Pair Camera Node**, select North/East/South/West and generate
   that direction's QR. Scan a different direction on each phone.
4. Verify that both a connection and **fresh frames** appear. A registered node alone
   does not prove that its camera is capturing.
5. Use Start/Stop to control all nodes, or Disconnect Slot to disconnect a direction.

The combined service uses port **8000 for both REST and camera WebSocket**.
Phone `localhost` means the phone itself. When automatic address selection chooses
the wrong adapter, put `CAMERA_PUBLIC_HOST=YOUR_LAPTOP_LAN_IP` in a root `.env` file.
Generate new QR codes after changing the address or port.

## Architecture and data meanings

```text
Android JPEG samples -> /ws/camera -> latest frame per direction
  -> shared configurable YOLO detector -> independent per-camera ByteTrack
  -> vehicle state / PCE / waiting estimates -> fair clockwise adaptive scheduler
  -> /ws/telemetry + /api/v1/cameras/{direction}/feed -> React dashboard
```

- Mobile profiles target 2 (low power) or 4 (balanced) JPEG samples/second per
  phone, with a 640-pixel default longest edge and preserved aspect ratio. One
  processed frame is allowed in flight. This is not a 30 FPS video transport.
- Each camera covers **one approach**. All detected supported vehicles in its frame
  belong to that approach. Aim/crop cameras accordingly; arbitrary quadrant ROIs
  are no longer drawn on approach feeds.
- Live vehicles are current tracked objects. Session counts are confirmed track
  observations, not daily totals, unique citywide vehicles or crossing-line counts.
- Queue is stopped vehicles; wait is estimated maximum stopped time; PCE is a
  weighted vehicle count. Camera movement and occlusion can affect these estimates.
- Displayed priority is the scheduler's score for the current decision, including
  fairness, rather than a separate invented dashboard formula.
- Each direction becomes stale independently after 3 seconds without a processed
  frame. Missing input shows unavailable/offline; it does not silently play demo video.
- Signal timing advances independently of incoming frames. The dashboard shows
  all-red when stopped or when all camera input is unavailable.
- Battery, signal strength and device temperature remain unavailable unless measured.
  Historical charts and efficiency improvement are not fabricated.
- Settings Save applies confidence and green-time limits to the runtime. Timing
  limits take effect at the next phase. Runtime settings reset on server restart;
  theme and notification preferences stay in the browser.

The supplied COCO model supports bicycles, cars, motorcycles, buses and trucks. Emergency
recognition and reinforcement learning are **not implemented**. ESP32 is kept in
simulation in the combined and split web runtimes.

The laptop profile uses a detector floor of 0.08 and ByteTrack high/new-track
thresholds of 0.15. This lets ByteTrack use weak boxes to maintain an existing
vehicle through occlusion without allowing every weak box to create a new count.
These values were calibrated on a small UVH-26 validation sample and still require
full validation before deployment.

For the production detector, prepare the real IISc UVH-26 traffic-camera dataset
and fine-tune YOLO26n using [the model training guide](docs/MODEL_TRAINING.md).
The runtime discovers supported classes from the loaded model, so 14-class
fine-tuned weights work without hard-coded COCO class IDs.

## Optional split deployment

Docker Compose defines Redis, REST on 8000, camera/telemetry WebSocket on 8001,
and Vite on 5173. Stop the combined server before using the same REST port.

```powershell
$env:CAMERA_PUBLIC_HOST = 'YOUR_LAPTOP_LAN_IP'
docker compose up --build
```

Open http://localhost:5173. This topology uses retained Redis snapshots and JPEGs
with expiration, plus acknowledged runtime commands; it does not create a second
perception pipeline in the REST process. Redis connection recovery is automatic.
Docker was not available on the repair machine; the shared Redis contract was
tested with fakeredis, not a running Docker deployment.

For UI development against the combined server:

```powershell
cd web-ui
npm run dev
```

The development server defaults to the combined backend and WebSocket runtime on
8000. Set `VITE_WS_TARGET=ws://localhost:8001` only for the split deployment.
Browser API and WebSocket URLs are relative so the dashboard also works from another computer.

## Validate

```powershell
.\.venv\Scripts\python.exe -m pytest -q --timeout=60
.\.venv\Scripts\python.exe scripts/smoke_runtime.py
.\.venv\Scripts\python.exe scripts/benchmark_runtime.py --pid SERVER_PID --images path/to/real-traffic-images --seconds 60 --fps 4 --output docs/benchmarks/local-four.json
.\.venv\Scripts\python.exe scripts/evaluate_detector.py --data datasets/uvh26/traffic.yaml
cd web-ui
npm run build
npm audit
```

Run the smoke test with the combined service already listening on 8000. It creates
four temporary camera clients using a real street-photo fixture, checks independent staleness and exercises
Stop/Start; run it when no real phones are connected. It does not measure detector
accuracy. Physical phone capture/endurance and annotated traffic accuracy tests
remain required; see the validation report.
