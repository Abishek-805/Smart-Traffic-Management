# Agent Rules

Before writing code:

1. Read PROJECT_CONTEXT.md

2. Do not redesign the architecture.

3. Prefer extending existing modules.

4. Never create duplicate pipeline classes.

5. Never hardcode demo videos.

6. Always ask the user whether to use:

- Demo Videos
- Mobile Cameras
- USB Cameras

7. Always ask whether ESP32 should be connected.

8. Keep TrafficPipeline independent from the Dashboard.

9. Keep ControlManager responsible for logging and hardware.

10. Preserve all existing tests.