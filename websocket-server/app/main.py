import asyncio
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI
from app.config import SERVER_NAME, VERSION, PORT, REDIS_URL
from server.websocket_server import camera_websocket_endpoint, message_handler
from server.runtime import start_runtime, stop_runtime, telemetry_websocket_endpoint, handle_command
from app.services.redis_broadcaster import WebSocketRedisBroadcaster

redis_broadcaster = WebSocketRedisBroadcaster(redis_url=REDIS_URL)

@asynccontextmanager
async def lifespan(app):
    await redis_broadcaster.connect()
    task = await start_runtime(message_handler, redis_broadcaster.publish_telemetry)
    commands = asyncio.create_task(redis_broadcaster.start_listener(handle_command))
    try:
        yield
    finally:
        commands.cancel()
        with suppress(asyncio.CancelledError):
            await commands
        await stop_runtime(task, message_handler)
        await redis_broadcaster.close()

app = FastAPI(title=SERVER_NAME, version=VERSION, lifespan=lifespan)
app.add_api_websocket_route("/ws/camera", camera_websocket_endpoint)
app.add_api_websocket_route("/ws/telemetry", telemetry_websocket_endpoint)
def get_app():
    return app
