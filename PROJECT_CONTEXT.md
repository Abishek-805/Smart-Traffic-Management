# Smart Traffic Management System

## Project Overview

This project is a Final Year Engineering Project.

The objective is to build a real-time adaptive traffic signal controller using Computer Vision and Artificial Intelligence.

The system is NOT a traffic simulator.

It controls a real traffic intersection prototype using an ESP32.

---

# System Architecture

4 Mobile Cameras
        │
        ▼
Main Laptop
        │
        ▼
YOLO11 Vehicle Detection
        │
        ▼
ByteTrack Tracking
        │
        ▼
Lane Assignment
        │
        ▼
Vehicle State Manager
        │
        ▼
Traffic Analytics
        │
        ▼
Intersection State
        │
        ▼
Priority Calculator
        │
        ▼
Fairness Manager
        │
        ▼
Signal Scheduler
        │
        ▼
Signal Decision
        │
        ▼
Hardware Command
        │
        ▼
ESP32
        │
        ▼
Traffic LEDs
Countdown Timer

---

# Current Project Status

Completed:

- Multi-camera architecture
- CameraManager
- YOLO integration
- ByteTrack
- Lane analytics
- IntersectionState
- Decision Engine
- Pipeline Health
- Dashboard
- ControlManager
- Decision Logger
- Hardware Interface

Remaining:

- Real mobile camera connection
- ESP32 serial communication
- Live testing
- Documentation

---

# Camera Requirements

The system MUST support four independent cameras.

Expected sources:

North Camera

South Camera

East Camera

West Camera

Camera sources can be:

- Mobile IP Camera
- USB Camera
- RTSP Stream
- Webcam

Video files are ONLY for development.

The application MUST ask the user which source to use.

Example:

1. Demo Mode (Video Files)

2. Mobile Cameras

3. USB Cameras

The application should NOT automatically load demo videos unless Demo Mode is selected.

---

# ESP32 Requirements

The application MUST detect available COM ports.

If an ESP32 is connected:

Prompt:

Select ESP32 Port

Available:

COM3

COM5

COM8

If none exists:

Run in Simulation Mode.

Simulation Mode is only a fallback.

It is NOT the primary operating mode.

---

# Dashboard Requirements

Remove placeholder text.

Display:

Project Name

Current Phase

Green Lane

Countdown Timer

Decision Reason

Pipeline Health

Camera Status

ESP32 Status

Decision History

Current FPS

Vehicle Count

Queue Time

PCE

No "???" placeholders should remain.

---

# AI Rules

Never replace live camera streams with virtual videos unless Demo Mode is selected.

Never replace ESP32 with simulation unless no hardware exists.

Never modify the Decision Engine logic.

Never modify the Priority Calculator.

Never modify the Scheduler.

Never modify the HardwareCommand format.

---

# Future Development Rules

Preserve the existing architecture.

Do not redesign the pipeline.

Do not merge unrelated modules.

Maintain separation between:

Camera

Pipeline

ControlManager

Dashboard

Hardware

---

# Success Criteria

A successful run should follow this flow:

Application Starts

↓

Ask Camera Source

↓

Connect Cameras

↓

Ask ESP32 Port

↓

Connect ESP32

↓

Start AI

↓

Display Dashboard

↓

Detect Vehicles

↓

Track Vehicles

↓

Compute Analytics

↓

Generate Signal Decisions

↓

Send Commands to ESP32

↓

Update LEDs

↓

Repeat
