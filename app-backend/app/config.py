import os

APP_NAME = "Smart Traffic Management System — App Backend"
VERSION = "2.0.0"
PORT = int(os.getenv("APP_BACKEND_PORT", os.getenv("PORT", "8000")))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

