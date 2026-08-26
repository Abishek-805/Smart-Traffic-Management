import os

SERVER_NAME = "Smart Traffic Management System — WebSocket Server"
VERSION = "2.0.0"
PORT = int(os.getenv("WEBSOCKET_SERVER_PORT", os.getenv("PORT", "8001")))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
PROTOCOL_VERSION = "1.0"

