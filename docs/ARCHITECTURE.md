# ARCHITECTURE.md

# Smart Traffic Management System
## Software Architecture Documentation

Version: 1.0

Status: Architecture Frozen (Sprint 6)

---

# 1. Project Goal

The Smart Traffic Management System is a real-time AI-powered adaptive traffic signal controller.

The objective is to analyse live traffic from **four independent cameras**, estimate congestion, compute signal priorities, and control a physical traffic light prototype using an ESP32.

The project is **NOT** a traffic simulator.

The software must always prioritise:

- Live Cameras
- Real AI Processing
- Real ESP32 Hardware

Video files and simulation mode exist only for development and testing.

---

# 2. High-Level Architecture

```
                 4 Mobile Cameras
                        │
                        ▼
                CameraManager
                        │
                        ▼
               TrafficPipeline
                        │
        ┌───────────────┴────────────────┐
        ▼                                ▼
LaneProcessingResult              IntersectionState
                        │
                        ▼
              Signal Decision Engine
                        │
                        ▼
                 PipelineResult
                        │
                        ▼
                 ControlManager
        ┌──────────┬──────────────┬──────────────┐
        ▼          ▼              ▼              ▼
 Dashboard    DecisionLogger  DecisionHistory  ESP32Interface
                                                │
                                                ▼
                                          Traffic Controller
```

---

# 3. System Layers

## Layer 1 — Camera Layer

Responsible for acquiring live video.

Modules

```
ai/camera/
```

Components

- CameraStream
- CameraManager
- StreamConfig

Responsibilities

- Connect cameras
- Read frames
- Monitor connection status
- Provide timestamps
- Calculate FPS
- Recover disconnected streams

Supports

- Mobile IP Cameras
- RTSP Cameras
- USB Cameras
- Webcam
- Demo Videos (Development Only)

The Camera Layer does NOT perform AI.

---

## Layer 2 — Perception Layer

Responsible for analysing frames.

Modules

```
ai/detection/
ai/tracking/
ai/lane/
ai/state/
ai/analytics/
```

Pipeline

```
Frame
    │
YOLO11 Detection
    │
ByteTrack
    │
Lane Assignment
    │
Vehicle State Manager
    │
Traffic Analytics
```

Each camera owns its own

- ByteTracker
- LaneManager
- VehicleStateManager
- AnalyticsExporter

YOLO Model is shared.

---

## Layer 3 — Processing Layer

Module

```
ai/pipeline/
```

Main class

```
TrafficPipeline
```

Responsibilities

- Process camera frames
- Run detection
- Run tracking
- Compute analytics
- Build LaneProcessingResult
- Build IntersectionState
- Execute Decision Engine
- Return PipelineResult

TrafficPipeline NEVER

- Displays UI
- Writes logs
- Communicates with hardware

---

## Layer 4 — Decision Layer

Modules

```
ai/decision/
```

Components

- PriorityCalculator
- FairnessManager
- EmergencyOverride
- SignalScheduler
- SignalController

Responsibilities

Generate

```
SignalDecision
```

Then

```
HardwareCommand
```

The decision algorithms are architecture frozen.

Do NOT modify these modules unless fixing bugs.

---

## Layer 5 — Control Layer

Module

```
ai/controller/
```

Main class

```
ControlManager
```

Responsibilities

Receive

```
PipelineResult
```

Then

- Log decisions
- Update dashboard
- Maintain history
- Send commands to ESP32

The Control Layer never performs AI.

---

## Layer 6 — Hardware Layer

Module

```
ai/hardware/
```

Components

- CommandEncoder
- ESP32Interface
- HardwareStatus

Responsibilities

Convert

```
HardwareCommand
```

into

- JSON
- Serial Protocol

Send to ESP32.

If ESP32 is unavailable

Switch to

```
Simulation Mode
```

without stopping the AI pipeline.

---

## Layer 7 — Presentation Layer

Module

```
dashboard/
```

Responsibilities

Display

- Four camera feeds
- Detection overlays
- Lane overlays
- Vehicle count
- Queue time
- PCE
- Current phase
- Countdown
- Decision reason
- Pipeline health
- Camera health
- Hardware status
- Decision history

Dashboard NEVER executes AI.

Dashboard only visualises PipelineResult.

---

# 4. Data Flow

```
CameraManager
        │
        ▼
TrafficPipeline
        │
        ▼
LaneProcessingResult
        │
        ▼
IntersectionState
        │
        ▼
SignalDecision
        │
        ▼
HardwareCommand
        │
        ▼
PipelineResult
        │
        ▼
ControlManager
        │
 ┌──────┼────────────┐
 ▼      ▼            ▼
HUD   Logger      ESP32
```

---

# 5. Important Data Models

## LaneProcessingResult

Represents processing results for one camera.

Contains

- raw frame
- annotated frame
- detections
- statistics
- timestamp
- fps
- connection status

---

## IntersectionState

Represents the entire intersection.

Contains

- lane statistics
- timestamp
- total vehicles
- active phase
- active green lane
- remaining time

---

## SignalDecision

Represents the selected traffic signal phase.

Contains

- selected lane
- duration
- reason
- priority score

---

## HardwareCommand

Represents commands sent to ESP32.

Contains

- lane
- green duration
- yellow duration
- phase id

---

## PipelineResult

Represents one complete AI cycle.

Contains

- lane processing results
- intersection state
- signal decision
- hardware command
- pipeline health

---

# 6. Runtime Sequence

```
Application Starts

↓

Select Camera Mode

↓

Connect Cameras

↓

Select ESP32 Port

↓

Connect ESP32

↓

Load YOLO Model

↓

Start Processing

↓

Read Frames

↓

Detect Vehicles

↓

Track Vehicles

↓

Assign Lanes

↓

Update Vehicle State

↓

Compute Analytics

↓

Create IntersectionState

↓

Decision Engine

↓

HardwareCommand

↓

PipelineResult

↓

ControlManager

↓

Dashboard

↓

Logger

↓

ESP32

↓

Repeat
```

---

# 7. Project Folder Structure

```
smart-traffic-system/

ai/
│
├── analytics/
├── camera/
├── controller/
├── decision/
├── detection/
├── hardware/
├── lane/
├── logging/
├── pipeline/
├── state/
├── tracking/
└── visualization/

dashboard/

config/

tests/

datasets/ (local real traffic data; ignored by Git)

logs/

main.py
```

---

# 8. Supported Camera Modes

The application must allow the user to choose the camera source.

```
1. Mobile IP Cameras

2. USB Cameras

3. RTSP Cameras

4. Webcam

5. Explicit real video files for offline replay
```

The system must NOT automatically use demo videos.

---

# 9. Supported Hardware Modes

```
Normal Mode

Laptop
    │
ESP32 Connected
    │
Traffic Controller
```

or

```
Simulation Mode

Laptop
    │
No ESP32
    │
Virtual Hardware
```

Simulation mode is only a fallback.

---

# 10. Architecture Rules

The following architecture is frozen.

Do NOT redesign.

Maintain the following separation:

```
Camera Layer

↓

Perception Layer

↓

Processing Layer

↓

Decision Layer

↓

Control Layer

↓

Hardware Layer

↓

Presentation Layer
```

No layer should directly access another non-adjacent layer.

---

# 11. Design Principles

- Single Responsibility Principle
- Modular Components
- Strongly Typed Data Models
- Dependency Separation
- Non-Blocking Hardware Communication
- Shared YOLO Model
- Independent Tracker per Camera
- Immutable Pipeline Outputs
- Dashboard as Consumer Only
- Hardware Layer Independent of AI

---

# 12. Future Work

Remaining implementation tasks

- Live mobile camera discovery
- Camera selection UI
- ESP32 COM port selection
- Automatic reconnection
- Hardware ACK handling
- Real intersection testing
- Performance optimisation
- Final documentation

No architectural redesign is expected.

Future work should extend the existing architecture rather than replacing it.

---

# 13. Architecture Freeze Notice

As of Sprint 6, the software architecture is considered stable.

Future development should focus on:

- Integration
- Testing
- Optimisation
- Hardware Validation
- Documentation

Core modules such as:

- TrafficPipeline
- PriorityCalculator
- FairnessManager
- SignalScheduler
- ControlManager
- HardwareCommand

should only be modified to fix defects or improve reliability—not to redesign their responsibilities.
