# Smart Traffic Management System
# Frontend Design Specification (FDS)

Version: 1.0.0

Document Status: Draft

Prepared By: OpenAI Solution Architecture

Target Frontend Stack:
- React 19+
- TypeScript
- Vite
- CSS Grid
- Context API
- WebSocket
- FastAPI Backend

Target Design Language

Traffic Operations Center (TOC)

Industrial SCADA

Mission Control

Municipal Intelligent Transportation Systems

---

# Revision History

| Version | Date | Author | Description |
|----------|------|---------|-------------|
| 1.0 | Initial | OpenAI | Initial Frontend Design Specification |

---

# Table of Contents

1. Executive Summary
2. Product Vision
3. Business Objectives
4. Project Scope
5. Stakeholders
6. User Personas
7. User Roles
8. Functional Requirements
9. Non-functional Requirements
10. Operational Principles
11. System Overview
12. Existing Backend Overview
13. Design Philosophy
14. UI Principles
15. Information Architecture
16. Success Metrics

(The remaining sections continue in later parts.)

---

# 1 Executive Summary

## Purpose

This document defines the complete frontend design specification for the Smart Traffic Management System.

It serves as the single source of truth for product designers, frontend developers, software architects, QA engineers, AI-assisted coding tools, and future contributors.

The document specifies how the frontend should function, behave, appear, communicate with the backend, and evolve over time.

This specification intentionally focuses only on the frontend application.

The backend services, AI perception pipeline, adaptive scheduler, ESP32 communication layer, and telemetry contracts already exist and are treated as stable interfaces.

No backend modifications are assumed by this specification.

---

## Primary Objectives

The frontend shall:

• Provide complete operational visibility.

• Display real-time traffic information.

• Present AI inference results clearly.

• Monitor hardware health.

• Visualize adaptive traffic control.

• Reduce operator workload.

• Support rapid incident response.

• Scale from one intersection to an entire city.

---

## Product Classification

The application is NOT:

• CRM

• ERP

• SaaS Dashboard

• Business Intelligence Tool

• Generic Analytics Dashboard

• Bootstrap Admin Template

Instead, the application is classified as:

Traffic Operations Center (TOC)

Industrial Human Machine Interface (HMI)

SCADA Monitoring Platform

Smart City Control Software

Real-Time Decision Support System

---

## Product Characteristics

The software must operate continuously for long periods.

Typical usage:

24 hours

7 days per week

365 days per year

Operators may spend 8–12 hours per shift using this interface.

The interface therefore prioritizes:

clarity

speed

predictability

minimal cognitive effort

consistent layouts

low visual fatigue

---

# 2 Product Vision

The Smart Traffic Management System enables municipalities to monitor and optimise traffic flow using artificial intelligence, computer vision, adaptive signal scheduling, and real-time telemetry.

Rather than acting as a passive dashboard, the application becomes an operational workspace where operators continuously observe, analyse, and respond to live traffic conditions.

The frontend should provide immediate answers to operational questions without requiring navigation between multiple screens.

An experienced operator should understand the current state of the intersection within two seconds of opening the application.

---

# 3 Business Objectives

The frontend contributes directly to the following organisational goals.

## Improve Traffic Flow

The interface shall display queue information clearly.

Operators should quickly identify congestion.

Signal timing should be understandable without opening secondary screens.

---

## Reduce Vehicle Waiting Time

Queue statistics should always remain visible.

Historical waiting trends should be accessible.

Adaptive phase decisions should be transparent.

---

## Improve Situational Awareness

Operators should never wonder:

Which direction currently has priority?

Which camera is offline?

Is AI working?

Is the controller connected?

How many vehicles are waiting?

These answers must always be visible.

---

## Improve Maintainability

The application shall encourage modular development.

Reusable components.

Reusable layouts.

Reusable data providers.

Reusable design tokens.

Minimal duplication.

---

## Future Expansion

Although the current deployment consists of a single intersection, the architecture shall support future deployment across:

multiple intersections

multiple districts

city-wide networks

regional traffic management centres

No redesign should be necessary to support these future deployments.

---

# 4 Project Scope

The frontend includes:

Dashboard

Live Camera Operations

Intersection Visualisation

Traffic Analytics

Operational Logs

Hardware Monitoring

AI Monitoring

Reports

Notifications

Settings

Authentication

User Management

Developer Tools

Diagnostics

The frontend excludes:

YOLO model implementation

ByteTrack implementation

Signal scheduling logic

ESP32 firmware

Database implementation

FastAPI backend logic

Machine learning training

---

# 5 Stakeholders

Primary Stakeholders

Traffic Operators

Responsible for continuous monitoring.

Traffic Engineers

Responsible for optimisation.

City Administrators

Responsible for system oversight.

Maintenance Engineers

Responsible for hardware health.

AI Engineers

Responsible for perception performance.

Developers

Responsible for software maintenance.

Researchers

Responsible for algorithm evaluation.

---

# 6 User Personas

## Persona 1

Traffic Operator

Responsibilities

Monitor intersection

Observe congestion

Verify signal operation

Respond to incidents

Primary Goals

Immediate awareness

Fast response

Reliable information

Low cognitive load

---

## Persona 2

Traffic Engineer

Responsibilities

Analyse congestion

Evaluate signal timing

Review historical performance

Primary Goals

Data analysis

Trend evaluation

Performance optimisation

---

## Persona 3

Maintenance Engineer

Responsibilities

Repair cameras

Monitor ESP32

Resolve network failures

Monitor hardware health

Primary Goals

Fast fault identification

Remote diagnostics

Device status

---

## Persona 4

AI Engineer

Responsibilities

Monitor detection quality

Validate tracking

Measure inference latency

Analyse dropped frames

Primary Goals

Model accuracy

Inference performance

Pipeline stability

---

# 7 User Roles

Operator

Read access

Acknowledges alerts

Views cameras

Views analytics

Cannot modify AI configuration.

---

Engineer

Includes Operator permissions.

Can restart devices.

Can modify runtime settings.

Can trigger diagnostics.

---

Administrator

Full system control.

User management.

Configuration management.

Report generation.

Role assignment.

---

Developer

Debug tools

Telemetry inspection

Developer overlays

Experimental feature flags

System diagnostics

Log streaming

---

# 8 Functional Requirements

FR-001

The dashboard shall display live intersection status.

FR-002

The application shall display four simultaneous camera feeds.

FR-003

The frontend shall receive telemetry using WebSockets.

FR-004

The interface shall automatically reconnect after connection loss.

FR-005

The application shall visualise queue lengths.

FR-006

The application shall display signal countdown timers.

FR-007

The application shall display adaptive phase information.

FR-008

The application shall indicate camera health.

FR-009

The application shall display backend health.

FR-010

The application shall display AI pipeline health.

FR-011

The application shall display ESP32 connection state.

FR-012

The application shall support historical analytics.

FR-013

The application shall support exporting reports.

FR-014

The application shall display operational logs.

FR-015

The application shall support dark mode.

FR-016

The application shall be keyboard accessible.

FR-017

The application shall maintain responsiveness during continuous telemetry.

FR-018

The application shall support future multi-intersection deployments.

(Functional requirements continue in later sections.)

---

# 9 Non-Functional Requirements

Availability

99.9%

Responsiveness

Dashboard updates should appear immediately after telemetry arrives.

Maintain smooth rendering under continuous updates.

Scalability

Support one intersection initially.

Architecture shall support hundreds without redesign.

Maintainability

Reusable components.

Strong typing.

Minimal duplication.

Accessibility

WCAG AA.

Keyboard navigation.

Colour-independent status indicators.

Performance

Dashboard should render comfortably at 60 FPS on modern desktop hardware.

Security

Authentication.

Role-based authorisation.

Secure API communication.

Reliability

Automatic recovery after temporary connection loss.

---

# 10 Operational Principles

The frontend exists to support operations, not presentation.

Every design decision should improve operator awareness.

The UI must avoid unnecessary decoration.

Animations should communicate state changes rather than serve aesthetic purposes.

Critical information should always remain visible.

No essential operational information should be hidden behind modal dialogs or excessive navigation.

The interface should prioritise consistency over novelty.

---

# 11 System Overview

The Smart Traffic Management System consists of several cooperating subsystems:

• Mobile Camera Application
• FastAPI Backend
• AI Perception Pipeline
• Adaptive Signal Scheduler
• ESP32 Traffic Controller
• WebSocket Telemetry Layer
• React Frontend

The frontend acts as the operator-facing presentation layer. It does not execute AI inference or control traffic signals directly. Instead, it visualises system state, health, and telemetry while sending authorised control requests through the backend.

---

<!-- END OF PART 1 -->

---

# 12 System Architecture

## 12.1 High-Level Architecture

The Smart Traffic Management System is composed of multiple independent but cooperating subsystems. Each subsystem has a clearly defined responsibility and communicates through stable interfaces.

The frontend shall never communicate directly with cameras, AI models, or ESP32 hardware. All communication flows through the FastAPI backend.

```text
                        +----------------------+
                        |   Traffic Operator   |
                        +----------+-----------+
                                   |
                                   |
                          React Frontend (SPA)
                                   |
                 REST API          |          WebSocket
                                   |
                     +-------------+--------------+
                     |        FastAPI Backend      |
                     +-------------+--------------+
                                   |
      +----------------------------+----------------------------+
      |             |              |             |              |
      |             |              |             |              |
 AI Pipeline    Scheduler      ESP32 Driver   Camera Hub   Database
      |                             |
 YOLO11 + ByteTrack           Traffic Controller
      |
Vehicle Detection
```

---

## 12.2 Major Subsystems

The application consists of six primary subsystems.

### Frontend

Responsibilities

Display operational information.

Display cameras.

Display AI status.

Display telemetry.

Display reports.

Display historical analytics.

Provide operator interaction.

Never perform business logic.

Never implement scheduling logic.

Never calculate adaptive phases.

---

### FastAPI Backend

Responsibilities

REST APIs

WebSocket APIs

Authentication

Telemetry aggregation

Camera management

Scheduler coordination

Hardware communication

Frontend should assume backend is the only trusted source of truth.

---

### AI Perception Pipeline

Responsibilities

Receive camera frames.

Run object detection.

Track detected vehicles.

Estimate queues.

Calculate occupancy.

Calculate traffic density.

Return structured lane statistics.

The frontend never performs AI inference.

---

### Scheduler

Responsibilities

Adaptive signal timing.

Countdown generation.

Green phase transitions.

Fairness.

Emergency overrides.

Scheduler operates independently from perception.

The frontend visualises scheduler state only.

---

### ESP32 Controller

Responsibilities

Physical traffic light control.

Signal acknowledgements.

Heartbeat.

Hardware diagnostics.

Communication health.

The frontend should never communicate directly with ESP32.

---

### Mobile Camera System

Responsibilities

Capture frames.

Compress images.

Transmit snapshots.

Maintain camera connection.

Report camera health.

Frontend visualises stream status.

---

# 13 Runtime Data Flow

## 13.1 Complete Runtime Lifecycle

Every frame follows this sequence.

```text
Camera

↓

Capture

↓

JPEG Compression

↓

HTTP Upload

↓

Backend Receiver

↓

YOLO11 Detection

↓

ByteTrack Tracking

↓

Lane Statistics

↓

Adaptive Scheduler

↓

Telemetry Generator

↓

WebSocket Broadcast

↓

React Context

↓

ViewModel

↓

UI Components
```

No frontend component should access intermediate processing stages.

Only backend-generated telemetry should be displayed.

---

## 13.2 Camera Lifecycle

Every mobile camera operates independently.

Lifecycle

CONNECTING

↓

CONNECTED

↓

STREAMING

↓

TEMPORARY LOSS

↓

RECONNECTING

↓

STREAMING

↓

OFFLINE

Each state should have a dedicated visual indicator.

---

## 13.3 Telemetry Lifecycle

Backend generates telemetry continuously.

Frontend receives:

Current signal phase

Remaining time

Lane queues

Vehicle counts

Frame timestamps

Pipeline health

Scheduler state

Camera health

Network latency

The frontend should update only the affected components.

Avoid full page re-rendering.

---

# 14 Backend Responsibilities

The backend owns all business logic.

Frontend owns presentation only.

Backend responsibilities include:

Vehicle detection

Vehicle tracking

Adaptive scheduling

Signal timing

Health monitoring

Telemetry generation

Camera registration

Hardware communication

Log aggregation

Historical data generation

Report generation

Configuration persistence

Authentication

Frontend responsibilities include:

Rendering

Interaction

Visualisation

Filtering

Sorting

Searching

Layout

Theme

Accessibility

Notifications

Dialogs

Local preferences

---

# 15 Frontend Responsibilities

The frontend must remain stateless regarding operational decisions.

Allowed responsibilities

Render dashboard

Render charts

Render cameras

Render reports

Show notifications

Export tables

Cache user preferences

Reconnect WebSockets

Animate UI

Forbidden responsibilities

Calculate queues

Calculate green phases

Modify AI outputs

Predict scheduler behaviour

Control ESP32 directly

Run AI inference

Modify telemetry

---

# 16 Runtime Communication

The frontend communicates using two mechanisms.

REST

Used for

Configuration

Reports

Historical data

Authentication

Settings

Manual commands

Diagnostics

WebSocket

Used for

Live telemetry

Camera updates

Health updates

Signal updates

Real-time logs

Alerts

Operator notifications

---

# 17 Frontend Runtime Flow

Application startup

↓

Load environment configuration

↓

Initialise Theme Provider

↓

Initialise Authentication

↓

Initialise Query Cache

↓

Initialise WebSocket Manager

↓

Load Dashboard

↓

Fetch initial REST data

↓

Open telemetry socket

↓

Receive live updates

↓

Update Context

↓

Update ViewModels

↓

Update affected UI components

Only changed components should re-render.

---

# 18 WebSocket Architecture

The frontend should maintain one logical connection for each stream type.

Example

Telemetry

Camera

Logs

Alerts

Health

Each connection should be managed by a dedicated service.

Example

```text
WebSocketManager

├── TelemetrySocket

├── CameraSocket

├── LogSocket

├── AlertSocket

└── HealthSocket
```

No React component should directly create WebSocket connections.

---

# 19 State Management Architecture

Application state should be divided into layers.

```text
Server State

↓

WebSocket

↓

Service Layer

↓

Context Providers

↓

ViewModels

↓

Presentation Components
```

Presentation components should never fetch data.

---

## 19.1 Global State

Examples

Current operator

Theme

Notifications

Connection status

User preferences

---

## 19.2 Feature State

Dashboard

Camera selection

Analytics filters

Logs filters

Report parameters

Settings form

---

## 19.3 Local Component State

Expanded panel

Hovered row

Dialog open

Search text

Selected tab

Temporary input

---

# 20 Folder Architecture

Recommended structure

```text
src/

app/

assets/

config/

contexts/

features/

hooks/

layouts/

pages/

router/

services/

shared/

styles/

theme/

types/

utils/

viewmodels/
```

Feature modules

```text
features/

dashboard/

devices/

analytics/

logs/

reports/

settings/

notifications/

ai-monitor/

hardware/

auth/
```

Each feature should contain

```text
components/

hooks/

pages/

services/

types/

viewmodels/
```

---

# 21 Component Architecture

Application

↓

Layout

↓

Feature Page

↓

Feature ViewModel

↓

Reusable Components

↓

Primitive Components

Example

Dashboard

↓

DashboardViewModel

↓

LaneGrid

↓

LaneCard

↓

MetricStrip

↓

StatusBadge

↓

Typography

No component should bypass ViewModels.

---

# 22 Service Layer

Every backend interaction belongs inside services.

Examples

TelemetryService

CameraService

SettingsService

AnalyticsService

LogsService

ReportsService

HealthService

AuthService

Components never call fetch() directly.

---

# 23 ViewModel Layer

ViewModels transform backend data into UI-friendly data.

Example

Backend

```json
{
  "queueLength":12,
  "remainingTime":18
}
```

ViewModel

```text
Heavy Queue

18 Seconds Remaining
```

Presentation components receive formatted values.

---

# 24 Error Recovery

Frontend should recover automatically.

Failures include

Backend unavailable

Camera disconnected

Pipeline stalled

Scheduler unavailable

ESP32 disconnected

WebSocket closed

Recovery strategy

Show warning

Attempt reconnect

Maintain previous valid state

Replace with loading skeleton if timeout exceeded

Never crash the application.

---

# 25 Performance Targets

Initial load

< 3 seconds

Dashboard render

< 100 ms

Telemetry update

< 16 ms

Camera latency display

Real-time

Animation

60 FPS target

Memory usage

Stable over 24-hour continuous operation

No memory leaks.

---

# 26 Logging Strategy

Frontend should categorise logs.

INFO

WARNING

ERROR

CRITICAL

SYSTEM

AI

CAMERA

NETWORK

ESP32

AUTH

Each log entry should include

Timestamp

Severity

Source

Category

Message

Optional metadata

---

# 27 Security Principles

Frontend shall never trust client-side data.

Always validate API responses.

Never expose secrets.

Never store tokens in plain text.

Protect privileged actions through role checks.

Display permission-denied messages gracefully.

---

# 28 Scalability

The UI must scale from:

1 intersection

↓

10 intersections

↓

100 intersections

↓

City-wide deployment

Adding a new intersection should require configuration, not redesign.

---

# 29 Architectural Principles

Single source of truth.

Separation of concerns.

Composition over inheritance.

Reusable components.

Strong typing.

Predictable state.

Responsive layouts.

Accessibility by default.

Performance first.

Operator-centric design.

No unnecessary complexity.

---

<!-- END OF PART 2 -->

---

# 30 Backend Integration Specification

## 30.1 Integration Philosophy

The frontend is a presentation layer.

The backend is the authoritative source of truth.

The frontend shall never attempt to derive business logic that already exists within the backend.

Every displayed value must originate from:

- REST API
- WebSocket Telemetry
- Configuration API

No values should be hardcoded except:

- Design tokens
- UI labels
- Static help text
- Default placeholder values

---

# 31 API Design Principles

All REST endpoints should follow a consistent design philosophy.

## HTTP Methods

GET

Retrieve information.

Never modify server state.

---

POST

Execute actions.

Create resources.

Restart devices.

Trigger reports.

Submit settings.

---

PUT

Replace an existing resource.

---

PATCH

Modify part of a resource.

---

DELETE

Remove a resource.

Only administrators may execute destructive operations.

---

# 32 REST Communication Strategy

Application startup should follow this sequence.

```text
Application Starts

↓

Load Environment

↓

Authenticate User

↓

GET System Health

↓

GET Current Configuration

↓

GET Camera List

↓

GET Dashboard Snapshot

↓

Open WebSockets

↓

Live Updates
```

The dashboard should never wait for WebSockets before rendering.

Instead:

REST provides the initial snapshot.

WebSockets provide continuous updates.

---

# 33 API Naming Convention

Good

/api/v1/system/health

/api/v1/cameras

/api/v1/dashboard

/api/v1/settings

/api/v1/reports

Avoid

/getHealth

/updateStatus

/loadDashboard

/action1

---

# 34 HTTP Status Code Handling

## 200

Operation successful.

Display data immediately.

---

## 201

Resource created.

Display success notification.

---

## 204

Operation successful.

No response body.

Refresh affected data.

---

## 400

Validation error.

Display field errors.

Do not retry.

---

## 401

Authentication required.

Redirect to Login.

---

## 403

Permission denied.

Display permission message.

Do not retry.

---

## 404

Resource not found.

Display empty state.

---

## 409

Conflict.

Refresh data.

Ask operator to retry.

---

## 422

Validation failure.

Highlight invalid inputs.

---

## 429

Too many requests.

Retry after delay.

---

## 500

Internal server error.

Display server unavailable message.

Allow manual retry.

---

## 503

Backend unavailable.

Show maintenance overlay.

Reconnect automatically.

---

# 35 REST Request Lifecycle

Every REST request should follow the same lifecycle.

```text
User Action

↓

Loading State

↓

HTTP Request

↓

Response

↓

Update State

↓

Update UI

↓

Toast (Optional)
```

Every request must support

Loading

Success

Failure

Timeout

Cancellation

Retry

---

# 36 Authentication Flow

Application Launch

↓

Check Existing Session

↓

If Invalid

↓

Login Screen

↓

Authentication API

↓

Receive Token

↓

Store Securely

↓

Load Dashboard

↓

Open WebSockets

The frontend should automatically redirect unauthenticated users.

---

# 37 WebSocket Lifecycle

```text
Disconnected

↓

Connecting

↓

Authenticating

↓

Connected

↓

Receiving Events

↓

Heartbeat

↓

Temporary Failure

↓

Reconnect

↓

Connected
```

Connection state should always be visible.

---

# 38 Connection States

Every live data source should expose one of the following states.

CONNECTING

ONLINE

STALE

RECONNECTING

OFFLINE

FAILED

Each state should have

Colour

Icon

Tooltip

Description

---

# 39 Dashboard Data Contract

Dashboard requires three data categories.

System

Traffic

Infrastructure

System

Backend

Scheduler

Pipeline

WebSocket

Traffic

Queues

Vehicle Counts

Signal Phase

Remaining Time

Congestion

Infrastructure

Camera Status

ESP32

Network

Hardware

---

# 40 Dashboard View Model

Dashboard should consume a single ViewModel.

DashboardViewModel

Contains

Application Status

Current Phase

Remaining Time

North Lane

South Lane

East Lane

West Lane

Camera Health

AI Health

Scheduler Health

ESP32 Health

Recent Alerts

Last Update Timestamp

No component should parse raw API responses.

---

# 41 Lane View Model

Each lane should expose

Lane Name

Direction

Vehicle Count

Queue Length

Average Waiting Time

Density

Occupancy

Current Signal

Camera Status

Last Frame

AI Confidence

Health

Severity

Display Status

---

Severity Rules

LOW

MEDIUM

HIGH

CRITICAL

Severity should influence colour and icon only.

Never change layout.

---

# 42 Camera View Model

Each camera should expose

Camera ID

Display Name

Connection Status

Resolution

FPS

Frame Age

Latency

Health

Snapshot URL

Last Update

AI Enabled

Recording State

Stream Status

Camera Preview URL

---

Camera States

Connecting

Online

Offline

Stale

Recovering

Maintenance

---

# 43 AI Pipeline View Model

Fields

Pipeline Healthy

YOLO Active

Tracker Active

Inference FPS

Average Inference Time

Dropped Frames

Detection Count

Tracking Count

Processing Errors

Last Processed Frame

Pipeline State

---

Pipeline States

Starting

Running

Paused

Recovering

Stalled

Failed

Offline

---

# 44 Scheduler View Model

Fields

Current Phase

Remaining Time

Cycle Time

Adaptive Enabled

Fairness Index

Queue Priority

Next Phase

Override Active

Emergency Mode

---

# 45 System Health View Model

Fields

Backend

WebSocket

Database

Scheduler

AI

ESP32

Cameras

CPU

Memory

Disk

Uptime

Version

Build

Environment

---

Health Levels

Healthy

Warning

Critical

Offline

Unknown

---

# 46 Alert Model

Every alert should contain

Unique ID

Timestamp

Severity

Source

Category

Title

Description

Acknowledged

Resolved

Operator

Metadata

Possible Actions

---

Severity Levels

Information

Low

Medium

High

Critical

Emergency

---

# 47 Notification Behaviour

Notification Types

Toast

Banner

Persistent Alert

Modal

Desktop Notification

Choose notification type based on severity.

Information

Toast

Warning

Banner

Critical

Persistent

Emergency

Modal

---

# 48 Retry Strategy

Automatic Retry

WebSockets

Health Checks

Camera Status

Telemetry

Manual Retry

Reports

Exports

Configuration

User Actions

---

Retry Timing

Attempt 1

Immediate

Attempt 2

2 Seconds

Attempt 3

5 Seconds

Attempt 4

10 Seconds

Maximum

30 Seconds

---

# 49 Caching Strategy

Never cache

Telemetry

Signal Phase

Queue Length

Remaining Time

Always cache

Settings

Theme

Operator Preferences

Reports Metadata

Configuration

Use short-term cache

Analytics

Camera List

Historical Data

---

# 50 Refresh Strategy

Dashboard

Real-time

Telemetry

Real-time

Camera Status

Real-time

Analytics

Manual Refresh

Reports

Manual Refresh

Logs

Streaming

Settings

On Demand

---

# 51 Error Handling Specification

Every screen must support

Loading

↓

Loaded

↓

Empty

↓

Error

↓

Retry

↓

Recovered

No screen should remain blank.

---

# 52 Loading Behaviour

Dashboard

Skeleton Layout

Camera

Placeholder Frame

Analytics

Skeleton Charts

Tables

Skeleton Rows

Settings

Disabled Form

Logs

Streaming Placeholder

---

# 53 Empty States

Examples

No Cameras

No Reports

No Logs

No Alerts

No Vehicles

No Historical Data

Each empty state should explain

Why

How to resolve

Next action

---

# 54 Timeout Behaviour

Request timeout

↓

Display timeout message

↓

Allow Retry

↓

Keep Previous Valid Data

Never replace valid data with blank content after timeout.

---

# 55 Accessibility Requirements

Every API failure should be announced.

Every loading indicator should include accessible text.

Every error should be keyboard reachable.

Focus should never be lost during updates.

---

# 56 API Versioning

All endpoints should use

/api/v1/

Future versions

/api/v2/

Frontend should isolate endpoint versions within the service layer.

Components must never hardcode endpoint URLs.

---

# 57 Service Responsibilities

AuthService

Authentication

DashboardService

Dashboard snapshot

CameraService

Camera management

AnalyticsService

Historical data

SettingsService

Configuration

LogsService

Logs

NotificationService

Alerts

HealthService

Health endpoints

TelemetryService

WebSocket telemetry

---

# 58 WebSocket Event Categories

Telemetry

Camera

Scheduler

Alerts

Logs

Health

Configuration

Notification

Every event should include

Timestamp

Event Type

Payload

Source

Version

---

# 59 Frontend Synchronisation Rules

REST establishes initial state.

WebSocket keeps state updated.

If WebSocket disconnects

Keep previous values

Mark as stale

Reconnect automatically

Do not clear dashboard.

---

# 60 Integration Success Criteria

A successful frontend integration should satisfy the following:

✓ No duplicated business logic.

✓ No direct hardware communication.

✓ No AI processing in the browser.

✓ Stable WebSocket recovery.

✓ Predictable REST communication.

✓ Strong typing between backend and frontend.

✓ Consistent loading states.

✓ Consistent error handling.

✓ Every UI component maps to a backend contract.

✓ Every operator action is traceable through a service layer.

---

<!-- END OF PART 3 -->

---

# 61 Information Architecture

## 61.1 Purpose

The information architecture defines how operators navigate the application and how information is grouped.

The navigation hierarchy shall prioritise operational workflows over software modules.

An operator should never need more than three interactions to reach any operational function.

---

## 61.2 Navigation Philosophy

Navigation should follow these principles:

• Frequently used features should always be visible.

• Rarely used features should be grouped.

• Critical information should never be hidden.

• Navigation should remain consistent across all pages.

• Operators should never lose context.

---

## 61.3 Primary Navigation

The application consists of the following primary modules.

```text
Dashboard

Live Cameras

Digital Twin

Analytics

Reports

Operations Logs

AI Monitor

Hardware Monitor

Notifications

Settings

Developer
```

---

## 61.4 Secondary Navigation

Each module may contain secondary tabs.

Example

Analytics

```
Overview

Traffic

Queue Analysis

Vehicle Types

Peak Hours

Historical Comparison

Exports
```

Hardware Monitor

```
Overview

ESP32

Cameras

Backend

Network

Storage

Performance
```

---

# 62 Application Layout

The application follows a persistent shell layout.

```
+-----------------------------------------------------------+
| Header                                                    |
+-----------+-----------------------------------------------+
|           |                                               |
| Sidebar   |              Main Workspace                   |
|           |                                               |
|           |                                               |
|           |                                               |
+-----------+-----------------------------------------------+
| Footer / Status Bar                                       |
+-----------------------------------------------------------+
```

The shell remains constant while only the workspace changes.

---

# 63 Header Specification

Purpose

Provide global system awareness.

The header shall contain

Application Logo

Current Operator

Current Time

Connection Status

Backend Status

AI Status

ESP32 Status

Notification Counter

Theme Toggle

User Menu

Global Search

Emergency Button

The header height should remain fixed.

---

# 64 Sidebar Specification

The sidebar provides module navigation.

Items

Dashboard

Live Cameras

Digital Twin

Analytics

Reports

Logs

Hardware

AI

Notifications

Settings

Developer

The sidebar should support

Collapsed Mode

Expanded Mode

Tooltips

Keyboard Navigation

Current Page Highlighting

Unread Indicators

---

# 65 Footer Status Bar

The footer continuously displays system health.

Items

Backend

AI

Scheduler

ESP32

Database

Network

WebSocket

Camera Count

Latency

FPS

Version

Environment

Every indicator updates live.

---

# 66 Dashboard Overview

Purpose

The Dashboard is the operational home screen.

It answers these questions immediately.

Is everything operational?

Which direction currently has priority?

Which camera is offline?

Is AI functioning?

Is the scheduler healthy?

How many vehicles are waiting?

Are there active alerts?

The dashboard should require no scrolling on a 1920×1080 display.

---

# 67 Dashboard Layout

```
+---------------------------------------------------------------+
| Global Header                                                 |
+---------------------------------------------------------------+

| System Health Bar                                             |

+---------------------------------------------------------------+

| Current Signal Phase                                          |

+---------------------------------------------------------------+

| NORTH CAMERA                                                  |

+---------------+-------------------------+---------------------+
|               |                         |                     |
| WEST CAMERA   |     DIGITAL TWIN        |    EAST CAMERA      |
|               |                         |                     |
+---------------+-------------------------+---------------------+

| SOUTH CAMERA                                                  |

+---------------------------------------------------------------+

| Lane Metrics                                                  |

+---------------------------------------------------------------+

| Recent Alerts                                                 |

+---------------------------------------------------------------+

| Status Footer                                                 |
```

---

# 68 Dashboard Components

The dashboard consists of the following components.

GlobalHeader

SystemHealthBar

SignalPhaseBar

NorthCamera

WestCamera

DigitalTwin

EastCamera

SouthCamera

LaneMetrics

AlertPanel

FooterStatusBar

No additional widgets should appear unless enabled.

---

# 69 Global Health Bar

Displays

Backend

AI

ESP32

Scheduler

Network

Database

Camera Health

Each status includes

Icon

Colour

Tooltip

Timestamp

Health State

Possible health values

Healthy

Warning

Critical

Offline

Unknown

---

# 70 Signal Phase Panel

Purpose

Visualise the active traffic phase.

Displays

Current Green Direction

Current Yellow Direction

Current Red Direction

Remaining Time

Cycle Time

Adaptive Status

Emergency Override

Manual Override

Next Phase

Countdown animation should be smooth.

---

# 71 Digital Twin

Purpose

Provide a spatial representation of the intersection.

Displays

Road Geometry

Traffic Lanes

Vehicles

Traffic Lights

Signal States

Queue Length

Vehicle Movement

Lane Direction

Camera Positions

Pedestrian Crossings

Future Reserved Areas

The Digital Twin must update using live telemetry.

---

# 72 Camera Panels

Each camera occupies an equal amount of screen space.

Each panel contains

Camera Name

Live Stream

Frame Timestamp

FPS

Latency

Connection State

AI Overlay Indicator

Fullscreen Button

Screenshot Button

Camera Settings Shortcut

Offline Overlay

Loading Skeleton

---

# 73 Camera Overlay

Overlay information

Current FPS

Latency

Frame Age

Resolution

Connection Status

Recording State

Detection Count

Tracking Count

Current Time

Camera ID

---

# 74 Lane Metrics

Each lane card displays

Direction

Vehicle Count

Queue Length

Average Wait Time

Occupancy

Density

Signal State

Current Priority

AI Confidence

Camera Health

Trend

Historical Comparison

---

# 75 Queue Visualisation

Queue severity

Low

Medium

High

Critical

Visualisation

Colour

Bar Length

Numeric Value

Trend Arrow

Historical Delta

---

# 76 Alert Panel

Displays

Latest Alerts

Critical Alerts

Warnings

System Messages

AI Messages

Camera Messages

ESP32 Messages

Each alert contains

Timestamp

Category

Severity

Title

Description

Acknowledged State

Operator

---

# 77 Devices Module

Purpose

Monitor every connected camera.

Displays

Video Wall

Camera Inspector

Health Information

Diagnostics

Restart Actions

Reconnect Actions

Firmware Version

Network Quality

Storage

---

## Layout

```
+-----------------------------------------------------+

| 2 × 2 Video Wall                                   |

+-----------------------------------------------------+

| Selected Camera Inspector                          |

+-----------------------------------------------------+

| Diagnostics                                         |

+-----------------------------------------------------+
```

---

# 78 Camera Inspector

Displays

Camera Name

Connection

Signal Strength

Battery

Temperature

Storage

Firmware

Uptime

Frame Age

Latency

Dropped Frames

Restart Button

Reconnect Button

Logs Shortcut

---

# 79 Analytics Module

Purpose

Provide historical insights.

Sections

Overview

Traffic Volume

Queue Analysis

Signal Efficiency

Peak Hours

Historical Comparison

Vehicle Classification

Reports

Exports

---

# 80 Analytics Dashboard

Charts

Hourly Traffic

Daily Traffic

Weekly Traffic

Monthly Traffic

Vehicle Classes

Average Wait

Average Queue

Signal Utilisation

Congestion Trend

Heat Map

Comparison Table

Charts should support

Zoom

Pan

Export

Fullscreen

Tooltip

Legend

Filtering

---

# 81 Operations Logs

Purpose

Provide chronological event history.

Features

Search

Filtering

Categories

Severity

Pause Stream

Export

Copy

Bookmark

Auto Follow

---

# 82 Log Entry

Each log entry includes

Timestamp

Severity

Category

Source

Message

Metadata

Correlation ID

Operator

---

# 83 Reports Module

Report Types

Daily

Weekly

Monthly

Custom

Vehicle Summary

Queue Summary

Signal Performance

System Health

Reports should support

PDF

CSV

Print

Email

Download

---

# 84 Notifications

Notification Centre

Contains

Unread

Acknowledged

Resolved

Dismissed

Categories

Traffic

System

Camera

Hardware

AI

Security

---

# 85 Settings

Settings Sections

General

Appearance

Traffic

AI

Camera

ESP32

Users

Roles

Notifications

Developer

Diagnostics

Each settings page should include

Description

Current Value

Default Value

Validation Rules

Reset Button

Save Button

---

# 86 Developer Module

Purpose

Provide engineering diagnostics.

Displays

WebSocket Inspector

REST Inspector

Telemetry Viewer

JSON Viewer

Performance Monitor

Component Tree

Context Viewer

Feature Flags

Debug Console

Build Information

This module should be hidden from standard operators.

---

# 87 Design Rules

Every screen should satisfy the following.

No unnecessary scrolling.

No duplicated information.

No hidden operational status.

Consistent spacing.

Consistent typography.

Consistent colours.

Responsive layout.

Keyboard accessible.

Screen-reader friendly.

Performance optimised.

---

<!-- END OF PART 4 -->

---

# 88 Design System

## 88.1 Purpose

The Design System establishes a single, reusable visual language for the entire Smart Traffic Management System.

Every page, component, dialog, chart, notification, and interaction shall use this design system.

The primary goals are:

- Consistency
- Readability
- Maintainability
- Accessibility
- High Information Density
- Low Cognitive Load

The design system should enable operators to recognise interface elements instantly without relearning patterns.

---

# 89 Design Philosophy

The interface should resemble professional operational software used in:

- Traffic Operations Centers
- Airport Control Towers
- Railway Control Centers
- Industrial SCADA
- Network Operations Centers (NOC)
- Emergency Dispatch Systems

The design should NOT resemble

- Bootstrap templates
- SaaS dashboards
- CRM software
- Marketing websites
- Mobile applications

---

# 90 Visual Language

The visual language should be

Professional

Industrial

Minimal

Functional

Stable

Dense

Readable

Predictable

Calm

Operators should feel confident rather than impressed.

The interface should communicate trust.

---

# 91 Colour System

Colours communicate operational state.

Colours are never decorative.

---

## Primary Colours

Primary Background

#101418

Application background.

---

Secondary Background

#171C22

Cards

Panels

Inspector sections

---

Surface

#20262D

Interactive containers.

---

Border

#2E3640

Separators

Cards

Tables

Inputs

---

Primary Text

#FFFFFF

Main content.

---

Secondary Text

#B0BAC5

Descriptions

Metadata

Secondary information.

---

Muted Text

#7E8791

Hints

Inactive labels

Disabled content

---

# 92 Status Colours

Healthy

#3FB950

Meaning

Operational

Running

Available

Connected

---

Warning

#F2C14E

Meaning

Needs attention

Queue building

Temporary issue

---

Critical

#E5534B

Meaning

Immediate operator attention required.

---

Offline

#5C6670

Meaning

Unavailable

Disconnected

No data

---

Information

#4EA8DE

Meaning

General status

Informational

---

AI

#A371F7

Used exclusively for AI features.

---

Network

#00B4D8

Network indicators.

---

Camera

#7DD3FC

Camera indicators.

---

ESP32

#FF7B54

Hardware controller.

---

# 93 Colour Usage Rules

Green never indicates selection.

Green always means healthy.

Red never indicates selection.

Red always indicates failure.

Yellow indicates degraded operation.

Grey indicates unavailable.

Blue indicates informational status.

Purple indicates AI.

---

# 94 Typography

Font Family

Inter

Fallback

Segoe UI

Roboto

Arial

sans-serif

---

# 95 Typography Scale

Display

36px

Dashboard headings

---

Heading 1

30px

Major pages

---

Heading 2

24px

Panels

---

Heading 3

20px

Sections

---

Heading 4

18px

Cards

---

Body Large

16px

---

Body

14px

Primary content.

---

Caption

12px

Metadata.

---

Micro

10px

Badges

Camera overlays

Timestamps

---

# 96 Typography Rules

Avoid all-uppercase paragraphs.

Maximum two font weights per panel.

Never exceed three font sizes inside one card.

Numbers should align vertically.

Timers should use tabular numbers.

---

# 97 Spacing System

Base Unit

8px

Spacing Scale

4

8

12

16

24

32

40

48

64

96

No arbitrary spacing values.

---

# 98 Border Radius

Small

4px

Medium

8px

Large

12px

Maximum

16px

Avoid excessive rounding.

---

# 99 Elevation

Level 0

Background

---

Level 1

Panels

---

Level 2

Dialogs

---

Level 3

Critical alerts

---

Shadows should remain subtle.

Never use excessive glow.

---

# 100 Grid System

Desktop

12-column grid.

Panel spacing

16px

Outer margin

24px

Maximum width

Fluid

Supports

1920

2560

3840

---

# 101 Responsive Breakpoints

Large Desktop

≥1920px

Desktop

1600–1919px

Laptop

1280–1599px

Tablet

768–1279px

Mobile

Future only

The application is desktop-first.

---

# 102 Icons

Preferred Library

Lucide

Alternative

Material Symbols

Icons should be

Simple

Outlined

Consistent

No filled icons unless required.

---

# 103 Button Design

Button Types

Primary

Secondary

Danger

Ghost

Icon

Toolbar

Split Button

Loading Button

---

Primary Button

Used for

Save

Generate

Restart

Export

---

Danger Button

Used only for

Delete

Shutdown

Emergency Override

---

# 104 Button States

Default

Hover

Pressed

Focused

Loading

Disabled

Success

Error

All states require keyboard focus styling.

---

# 105 Input Components

Text Input

Number Input

Dropdown

Search

Checkbox

Radio

Toggle

Slider

Date Picker

Time Picker

Textarea

Password

Every input requires

Validation

Error message

Helper text

Focus state

---

# 106 Status Badge

Displays

Healthy

Warning

Offline

Critical

Unknown

Properties

Colour

Icon

Text

Tooltip

Timestamp

Status badges should never blink.

---

# 107 Metric Card

Purpose

Display one operational metric.

Structure

Title

Value

Unit

Trend

Delta

Timestamp

Status

Metric cards should avoid decorative graphics.

---

# 108 Camera Widget

Displays

Live image

Camera name

FPS

Latency

Frame age

Health

Resolution

Recording state

Detection count

Tracking count

Expandable preview

Camera widgets should preserve aspect ratio.

---

# 109 Tables

Support

Sorting

Filtering

Searching

Column resizing

Sticky header

Pagination

CSV export

Keyboard navigation

Tables should avoid horizontal scrolling.

---

# 110 Charts

Supported

Line

Bar

Area

Pie

Heatmap

Timeline

Scatter

Histogram

Stacked Bar

Charts must include

Legend

Tooltip

Export

Zoom

Reset

Axis labels

Units

---

# 111 Notifications

Toast

Short-lived

Banner

Persistent

Modal

Critical

Notification Center

Historical

Every notification should include

Severity

Time

Source

Description

Recommended action

---

# 112 Dialogs

Confirmation

Delete

Restart

Reconnect

Generate Report

Settings

Emergency Override

Dialogs should never hide critical telemetry.

---

# 113 Empty States

Every empty state should include

Illustration

Reason

Suggested action

Documentation link

Retry button

---

# 114 Loading States

Skeleton screens

Progress bars

Spinner

Estimated duration

Loading text

Avoid blank screens.

---

# 115 Animations

Animations communicate change.

Never decorate.

Duration

100ms

150ms

250ms

Maximum

300ms

Avoid bounce animations.

---

# 116 Accessibility

Target

WCAG 2.2 AA

Support

Keyboard

Screen readers

High contrast

Reduced motion

Visible focus

ARIA labels

Semantic HTML

---

# 117 Component Library

Core Components

Button

Badge

Chip

Card

Panel

Drawer

Dialog

Tooltip

Dropdown

Tabs

Accordion

Timeline

Tree View

Table

Chart

Camera

Status Bar

Health Indicator

Metric Card

Lane Card

Digital Twin

Video Wall

Notification

Log Viewer

Report Viewer

Inspector

Progress Bar

Breadcrumb

Command Palette

Context Menu

Every component should be reusable.

---

# 118 Layout Components

AppShell

Header

Sidebar

Workspace

Inspector

Panel

Split View

Footer

Toolbar

Grid

Stack

Container

Section

---

# 119 Theme Tokens

All visual values should come from design tokens.

Example

colors.background.primary

colors.status.healthy

spacing.md

radius.small

font.body

animation.fast

Components should never hardcode colours.

---

# 120 Design System Success Criteria

The design system is successful if

✓ Every page looks consistent.

✓ Every component is reusable.

✓ Colours always communicate meaning.

✓ Typography remains readable after long use.

✓ Components are interchangeable.

✓ Themes can be modified centrally.

✓ Future pages require minimal new styles.

✓ Accessibility is maintained by default.

✓ The application resembles professional operational software rather than a consumer dashboard.

---

<!-- END OF PART 5 -->

---

# 121 Frontend Software Architecture

## 121.1 Purpose

The frontend architecture defines how the application is organised, how modules communicate, and how responsibilities are separated.

The architecture must remain scalable as the system grows from a single intersection to a city-wide deployment.

Primary goals

- Maintainability
- Scalability
- Reusability
- Performance
- Testability
- Predictability

---

# 122 Architectural Principles

The frontend follows these principles.

Single Responsibility Principle

Each module performs one responsibility.

---

Feature-Based Architecture

Business features remain isolated.

---

Strong Typing

Every API response is strongly typed.

---

Separation of Concerns

UI

↓

ViewModel

↓

Service

↓

API

↓

Backend

---

Composition

Reusable components should be composed rather than inherited.

---

Predictable State

Application state should always have a single owner.

---

# 123 Recommended Project Structure

```
src/

app/

assets/

config/

contexts/

features/

hooks/

layouts/

router/

services/

shared/

styles/

theme/

types/

utils/

viewmodels/

main.tsx
```

---

# 124 App Layer

Responsible for

Application bootstrap

Theme

Routing

Providers

Global initialization

Contents

```
app/

App.tsx

AppProviders.tsx

ErrorBoundary.tsx

AppInitializer.tsx
```

---

# 125 Config Layer

Contains

Environment configuration

Application constants

Feature flags

Route configuration

API configuration

WebSocket configuration

```
config/

api.ts

app.ts

routes.ts

features.ts

environment.ts
```

---

# 126 Feature Layer

Every business feature owns itself.

```
features/

dashboard/

devices/

analytics/

logs/

reports/

notifications/

settings/

hardware/

ai-monitor/

authentication/

developer/
```

Every feature contains

```
components/

pages/

hooks/

services/

types/

viewmodels/
```

A feature should never directly modify another feature.

---

# 127 Shared Layer

Contains reusable functionality.

```
shared/

components/

icons/

hooks/

utils/

types/

constants/

animations/
```

Shared components contain no business logic.

---

# 128 Theme Layer

Contains

Colour tokens

Typography

Spacing

Breakpoints

Elevation

Animation timings

Status colours

Component variants

No page should define colours directly.

---

# 129 Services Layer

Every backend communication belongs here.

Example

```
services/

api/

dashboard/

camera/

telemetry/

analytics/

settings/

reports/

logs/

authentication/
```

Responsibilities

REST

WebSocket

Caching

Retry

Authentication

Parsing

Error handling

No UI code.

---

# 130 API Client

Every HTTP request passes through one API client.

```
ApiClient

↓

Authentication

↓

Request

↓

Interceptor

↓

Response

↓

Parser

↓

Typed Model
```

The client handles

Authorization

Retries

Timeouts

Errors

Logging

JSON parsing

---

# 131 WebSocket Manager

Only one manager should exist.

```
WebSocketManager

├── Telemetry

├── Camera

├── Logs

├── Alerts

├── Notifications

└── Health
```

Responsibilities

Reconnect

Heartbeat

Authentication

Queue messages

Reconnect strategy

Connection health

---

# 132 Context Providers

Global state belongs here.

Example

```
ThemeContext

↓

AuthContext

↓

NotificationContext

↓

TelemetryContext

↓

CameraContext

↓

SettingsContext
```

Contexts should never perform rendering.

---

# 133 State Ownership

Every piece of state has one owner.

Theme

ThemeContext

Authentication

AuthContext

Telemetry

TelemetryContext

Settings

SettingsContext

Dashboard Filters

DashboardViewModel

Dialog Visibility

Local Component

---

# 134 ViewModel Layer

Purpose

Convert backend models into UI models.

Backend

```
queueLength

waitingTime

signalState
```

↓

ViewModel

```
Heavy Queue

34 Vehicles

18 Second Wait
```

Presentation components should never perform formatting.

---

# 135 Hooks

Reusable logic belongs inside hooks.

Examples

```
useTelemetry()

useCamera()

useReports()

useAnalytics()

useNotifications()

useSignalPhase()

useIntersection()

useCurrentTime()

useSettings()
```

Hooks should never contain presentation.

---

# 136 Component Hierarchy

```
Application

↓

Layout

↓

Feature Page

↓

Feature Section

↓

Panel

↓

Reusable Component

↓

Primitive Component
```

Example

```
Dashboard

↓

LaneGrid

↓

LaneCard

↓

MetricChip

↓

StatusBadge

↓

Typography
```

---

# 137 Primitive Components

The smallest reusable elements.

Examples

Button

Icon

Label

Badge

Avatar

Divider

Spinner

Tooltip

Progress

Checkbox

Input

Primitive components contain no application knowledge.

---

# 138 Composite Components

Examples

CameraPanel

LaneCard

HealthPanel

NotificationCard

ReportTable

AnalyticsChart

InspectorPanel

Composite components combine primitives.

---

# 139 Smart Components

Examples

Dashboard

Analytics

Logs

Devices

Settings

These consume ViewModels.

They may coordinate multiple child components.

---

# 140 Page Components

Every route owns one page.

Example

```
DashboardPage

DevicesPage

AnalyticsPage

LogsPage

ReportsPage

SettingsPage
```

Pages should remain lightweight.

---

# 141 Routing

Recommended

```
/

/dashboard

/devices

/digital-twin

/analytics

/logs

/reports

/hardware

/ai

/settings

/developer
```

Routes should support lazy loading.

---

# 142 Lazy Loading

Lazy load

Analytics

Reports

Developer

Settings

Do not lazy load

Dashboard

Telemetry

Camera Operations

Authentication

---

# 143 Error Boundaries

Each feature should have its own boundary.

```
Application

↓

Dashboard Boundary

↓

Analytics Boundary

↓

Settings Boundary

↓

Developer Boundary
```

Failure in one module should not crash others.

---

# 144 Performance Optimisation

Avoid unnecessary renders.

Use

React.memo()

useMemo()

useCallback()

Virtualized tables

Lazy loading

Memoized selectors

Context splitting

Avoid

Large global state

Anonymous callbacks

Deep prop drilling

Massive components

---

# 145 WebSocket Update Strategy

Incoming message

↓

Validate

↓

Parse

↓

Update Store

↓

Update ViewModel

↓

Re-render affected components

Only changed data should trigger rendering.

---

# 146 Folder Naming Convention

Use

camelCase

PascalCase

Consistent naming

Examples

```
LaneCard.tsx

CameraPanel.tsx

DashboardPage.tsx

TelemetryService.ts

NotificationContext.tsx
```

Avoid

Component1.tsx

newCard.tsx

temp.tsx

---

# 147 File Size Guidelines

React Component

Maximum

250 lines

ViewModel

Maximum

300 lines

Service

Maximum

300 lines

Hook

Maximum

200 lines

Utility

Maximum

150 lines

Large files should be split.

---

# 148 Testing Strategy

Every feature should include

Unit Tests

Integration Tests

Component Tests

End-to-End Tests

Examples

```
Dashboard.test.tsx

CameraPanel.test.tsx

TelemetryService.test.ts

NotificationContext.test.tsx
```

---

# 149 Coding Standards

Use

Strict TypeScript

ESLint

Prettier

Husky

Conventional Commits

Meaningful variable names

Pure functions

No duplicated logic

Document exported APIs.

---

# 150 Frontend Success Criteria

The frontend architecture is considered successful if:

✓ Every feature is isolated.

✓ Every component is reusable.

✓ Backend communication exists only in the service layer.

✓ ViewModels isolate presentation logic.

✓ State ownership is predictable.

✓ WebSockets reconnect automatically.

✓ Performance remains stable during continuous telemetry.

✓ Components remain independently testable.

✓ The codebase scales cleanly as additional intersections, devices, and operational features are added.

---

<!-- END OF PART 6 -->

---

# 151 User Experience Specification

## 151.1 UX Philosophy

The Smart Traffic Management System is not a reporting dashboard.

It is an operational workspace.

Every interaction should help an operator answer one of four questions.

1. What is happening?
2. Is something wrong?
3. What action is required?
4. What will happen next?

Every screen shall minimise operator cognitive load while maximising situational awareness.

---

# 152 User Journey

## 152.1 Operator Login

Operator opens application

↓

Authentication screen

↓

Credentials entered

↓

Authentication successful

↓

Load application shell

↓

Fetch initial configuration

↓

Load dashboard snapshot

↓

Open WebSocket connections

↓

Dashboard becomes live

Expected duration

< 3 seconds

---

## 152.2 Dashboard Workflow

Dashboard opens

↓

System health verified

↓

Camera previews visible

↓

Current signal phase displayed

↓

Lane queues visible

↓

Digital Twin updates

↓

Alerts streamed

↓

Operator monitors continuously

---

## 152.3 Camera Failure Workflow

Camera disconnects

↓

Backend detects failure

↓

WebSocket event

↓

Camera panel changes to

OFFLINE

↓

Last frame retained

↓

Recovery countdown begins

↓

Reconnect attempted

↓

Success

↓

Panel returns to LIVE

If unsuccessful

↓

Persistent alert generated

---

## 152.4 AI Pipeline Failure

Pipeline stalls

↓

Backend publishes event

↓

Pipeline status becomes

STALLED

↓

Dashboard highlights AI section

↓

Latest valid detections remain visible

↓

Operator receives notification

↓

Pipeline recovers

↓

Status returns to HEALTHY

---

## 152.5 ESP32 Disconnect

Controller unreachable

↓

Health event received

↓

ESP32 status becomes

OFFLINE

↓

Dashboard warning shown

↓

Operator opens Hardware Monitor

↓

Reconnect attempted

↓

Successful

↓

Status updated automatically

---

# 153 Loading Experience

Every page must have a loading strategy.

Never display a blank screen.

Dashboard

Skeleton layout

Camera

Placeholder image

Analytics

Skeleton charts

Reports

Progress indicator

Settings

Disabled controls

Logs

Loading timeline

---

# 154 Error Experience

Errors should explain

What happened

Why

Impact

Recommended action

Never display

Unknown Error

Instead display

Unable to connect to telemetry.

Retrying automatically.

---

# 155 Offline Behaviour

Temporary connection loss

↓

Display stale badge

↓

Retain latest data

↓

Reconnect

↓

Replace stale indicator

Never clear operational information immediately.

---

# 156 Notification Behaviour

Notification priorities

Information

Success

Warning

Critical

Emergency

Critical notifications require acknowledgement.

Emergency notifications remain visible until resolved.

---

# 157 Permissions

Operator

Dashboard

Devices

Analytics

Logs

Reports

Cannot change system configuration.

Engineer

Operator permissions

+

Restart hardware

Reconnect devices

Diagnostics

Administrator

Full access

Developer

Hidden tools

Telemetry inspector

Debug overlay

Feature flags

---

# 158 Accessibility Checklist

Keyboard navigation

Visible focus

Semantic HTML

Screen reader support

ARIA labels

Colour-independent indicators

Reduced motion support

Minimum contrast ratio

Resizable text

Accessible tables

Accessible charts

---

# 159 Performance Budget

Dashboard first render

<100 ms

Initial load

<3 s

Telemetry update

<16 ms

Camera status update

Immediate

Memory leaks

None

Continuous runtime

24/7

---

# 160 Security Guidelines

Use HTTPS.

Validate all API responses.

Store authentication securely.

Never expose secrets.

Never trust client-side permissions.

All privileged actions require backend authorisation.

---

# 161 Logging Standards

Frontend logs should include

Timestamp

Severity

Category

Message

Context

Correlation ID

Never log

Passwords

Tokens

Personal data

Secrets

---

# 162 Quality Assurance Checklist

Dashboard loads

Camera wall operational

Digital Twin updates

Signal countdown accurate

Telemetry reconnects

Offline state works

Notifications appear

Reports generate

Settings save

Accessibility verified

Performance budget met

---

# 163 Deployment

Environment

Development

Staging

Production

Each environment should provide

Environment label

API URL

WebSocket URL

Feature flags

Version number

Build timestamp

Git commit hash

---

# 164 CI/CD

Pipeline

Lint

↓

Type Check

↓

Unit Tests

↓

Integration Tests

↓

Build

↓

E2E Tests

↓

Deploy Staging

↓

Approval

↓

Deploy Production

No deployment should proceed if automated tests fail.

---

# 165 Future Roadmap

Phase 1

Single intersection

Phase 2

Multiple intersections

Phase 3

District monitoring

Phase 4

City-wide deployment

Phase 5

GIS integration

Phase 6

Emergency vehicle priority

Phase 7

Weather integration

Phase 8

Predictive AI congestion forecasting

Phase 9

Public transport priority

Phase 10

Smart city ecosystem integration

---

# 166 Coding Standards

React

Functional components only

Strict TypeScript

Reusable components

No duplicated logic

Feature-first architecture

Strong typing

ESLint

Prettier

Conventional commits

Document exported APIs.

---

# 167 Definition of Done

A feature is complete when

✓ UI implemented

✓ Responsive

✓ Accessible

✓ Connected to backend

✓ Loading state implemented

✓ Error state implemented

✓ Empty state implemented

✓ Offline state implemented

✓ Unit tests written

✓ Integration tests pass

✓ Documentation updated

---

# 168 Final Acceptance Criteria

The Smart Traffic Management System frontend shall

✓ Operate continuously in a Traffic Operations Center.

✓ Provide real-time situational awareness.

✓ Remain responsive under continuous telemetry.

✓ Support operators, engineers, and administrators.

✓ Scale from one intersection to city-wide deployment.

✓ Follow a consistent SCADA-inspired design language.

✓ Maintain accessibility and performance standards.

✓ Integrate seamlessly with the existing FastAPI backend, WebSocket telemetry, AI perception pipeline, and ESP32 traffic controller.

✓ Require no backend changes to deliver the intended user experience.

---

# Appendix A — Recommended Technology Stack

Frontend

- React 19+
- TypeScript
- Vite
- React Router
- Context API
- CSS Grid
- CSS Variables

UI

- Lucide Icons
- Recharts
- Framer Motion (minimal use)

Testing

- Vitest
- React Testing Library
- Playwright

Backend (existing)

- FastAPI
- WebSocket
- OpenCV
- YOLO11
- ByteTrack

---

# Appendix B — Glossary

AI
: Artificial Intelligence

ESP32
: Embedded microcontroller controlling traffic signals

FPS
: Frames Per Second

FDS
: Frontend Design Specification

HMI
: Human Machine Interface

PCE
: Passenger Car Equivalent

SCADA
: Supervisory Control and Data Acquisition

Telemetry
: Real-time operational data streamed from the backend

TOC
: Traffic Operations Center

WebSocket
: Persistent bidirectional communication protocol for live updates

YOLO11
: Real-time object detection model

ByteTrack
: Multi-object tracking algorithm

---

# Document Summary

Document Name

Frontend Design Specification

Version

1.0

Purpose

Define the architecture, design system, user experience, software architecture, operational workflows, and implementation guidelines for the Smart Traffic Management System frontend.

Target Audience

- Product Designers
- UX Designers
- Frontend Engineers
- Software Architects
- QA Engineers
- AI-assisted coding tools
- Project Maintainers

End of Specification.
