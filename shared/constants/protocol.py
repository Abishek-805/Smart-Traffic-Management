PROTOCOL_VERSION = "1.0"

DEFAULT_APP_BACKEND_PORT = 8000
DEFAULT_WEBSOCKET_SERVER_PORT = 8001
DEFAULT_REDIS_PORT = 6379

REDIS_CHANNELS = {
    "TELEMETRY": "channel:telemetry",
    "CAMERA_EVENTS": "channel:camera_events",
    "SYSTEM_COMMANDS": "channel:system_commands",
    "LOGS": "channel:logs",
}
