import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import SERVER_NAME, VERSION, PORT, REDIS_URL
from app.websocket.camera_handler import camera_websocket_endpoint, message_handler
from app.websocket.telemetry_handler import telemetry_websocket_endpoint, telemetry_clients
from app.services.redis_broadcaster import WebSocketRedisBroadcaster
from core.application_context import ApplicationContext
from ai.utils.logger import get_logger

logger = get_logger("WebSocketServer")

redis_broadcaster = WebSocketRedisBroadcaster(redis_url=REDIS_URL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {SERVER_NAME} v{VERSION} on port {PORT}...")
    ctx = ApplicationContext.get_instance()

    message_handler.session_manager = ctx.session_manager
    message_handler.connection_manager = ctx.connection_manager
    logger.info("WebSocket MessageHandler wired to ApplicationContext session/connection managers.")

    if ctx.pipeline is None:
        from ai.pipeline.traffic_pipeline import TrafficPipeline
        ctx.pipeline = TrafficPipeline(save_output=False)
    if ctx.control_manager is None:
        from ai.controller.control_manager import ControlManager
        ctx.control_manager = ControlManager(simulation_mode=True)
    logger.info("TrafficPipeline and ControlManager initialized in WebSocket Server.")

    await redis_broadcaster.connect()

    async def broadcast_telemetry(snapshot_data: dict):
        if redis_broadcaster.is_connected:
            await redis_broadcaster.publish_telemetry(snapshot_data)
            
        if not telemetry_clients:
            return
        now_ms = int(time.time() * 1000)
        payload_copy = dict(snapshot_data.get("payload", {}))
        payload_copy["broadcastTimestamp"] = now_ms
        
        cap_ts = payload_copy.get("captureTimestamp")
        if cap_ts:
            payload_copy["pipelineLatencyMs"] = now_ms - cap_ts
            
        snapshot_data["payload"] = payload_copy

        disconnected = set()
        for ws in telemetry_clients:
            try:
                await ws.send_json(snapshot_data)
            except Exception:
                disconnected.add(ws)
                
        for ws in disconnected:
            telemetry_clients.discard(ws)

    ctx.on_snapshot_updated = broadcast_telemetry

    async def handle_system_command(command: str, payload: dict):
        logger.info(f"Received Redis system command: '{command}'")
        if command == "START":
            ctx.system_running = True
        elif command == "STOP":
            ctx.system_running = False

    cmd_listener_task = asyncio.create_task(redis_broadcaster.start_listener(handle_system_command))

    yield
    logger.info(f"Shutting down {SERVER_NAME}...")
    cmd_listener_task.cancel()
    await redis_broadcaster.close()
    if ctx.pipeline:
        ctx.pipeline.release()
    if ctx.control_manager:
        ctx.control_manager.release()

app = FastAPI(
    title=SERVER_NAME,
    description="Dedicated Real-Time WebSocket Server & AI Perception Engine for Smart Traffic Management.",
    version=VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_api_websocket_route("/ws/camera", camera_websocket_endpoint)
app.websocket("/ws/telemetry")(telemetry_websocket_endpoint)

def get_app() -> FastAPI:
    return app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)
