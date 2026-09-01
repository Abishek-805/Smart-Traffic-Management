import asyncio
import json
from typing import Optional, Dict, Any, Callable
from ai.utils.logger import get_logger

logger = get_logger("AppBackendRedisService")

class AppBackendRedisService:
    """Redis Pub/Sub interface for App Backend."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.pubsub = None
        self.is_connected = False
        self.latest_telemetry: Optional[Dict[str, Any]] = None
        self.connected_nodes: Dict[str, Dict[str, Any]] = {}

    async def connect(self):
        try:
            import redis.asyncio as aioredis
            if self.redis_client:
                await self.redis_client.aclose()
            self.redis_client = aioredis.from_url(self.redis_url, decode_responses=True, socket_connect_timeout=2, socket_timeout=2)
            await self.redis_client.ping()
            self.is_connected = True
            logger.info(f"App Backend connected to Redis at '{self.redis_url}'")
        except Exception as e:
            logger.warning(f"App Backend Redis unavailable; split-service commands and telemetry are unavailable: {e}")
            self.is_connected = False

    async def publish_command(self, command: str, payload: Optional[Dict[str, Any]] = None):
        if not self.is_connected or not self.redis_client:
            raise RuntimeError("Redis unavailable; runtime command was not applied")
        try:
            from shared.constants.protocol import REDIS_CHANNELS
            from shared.events.event_types import EventTypes
            from shared.schemas.events import RedisEventEnvelope
            
            import uuid
            request_id = uuid.uuid4().hex
            payload = {**(payload or {}), "request_id": request_id}
            envelope = RedisEventEnvelope(
                event=EventTypes.SYSTEM_COMMAND,
                data={"command": command, "payload": payload or {}}
            )
            listeners = await self.redis_client.publish(REDIS_CHANNELS["SYSTEM_COMMANDS"], envelope.model_dump_json())
            if not listeners:
                raise RuntimeError("Camera runtime is offline")
            for _ in range(50):
                result = await self.redis_client.get("traffic:command:" + request_id)
                if result:
                    response = json.loads(result)
                    if response.get("status") != "SUCCESS":
                        raise RuntimeError(response.get("message", "Command rejected"))
                    return response
                await asyncio.sleep(0.1)
            raise RuntimeError("Runtime did not acknowledge the command")
        except Exception as e:
            raise RuntimeError(f"Runtime command failed: {e}") from e

    async def start_listener(self):
        # Retained snapshots survive late REST startup. TTL prevents stale success.
        import time
        import base64
        from core.application_context import ApplicationContext
        ctx = ApplicationContext.get_instance()
        while True:
            try:
                if not self.is_connected:
                    await self.connect()
                if self.is_connected:
                    raw = await self.redis_client.get("traffic:latest_snapshot")
                    if raw and time.time() - json.loads(raw)["data"].get("timestamp", 0) < 3:
                        self.latest_telemetry = json.loads(raw)["data"]
                        ctx.latest_snapshot = self.latest_telemetry
                        ctx.remote_received_at = time.monotonic()
                        payload = self.latest_telemetry.get("payload", {})
                        ctx.system_running = payload.get("systemRunning", False)
                        ctx.remote_nodes = payload.get("nodes", [])
                        for direction, lane in payload.get("lanes", {}).items():
                            encoded = await self.redis_client.get("traffic:frame:" + direction)
                            if encoded and lane.get("streamStatus") == "LIVE":
                                ctx.frame_buffer[direction] = base64.b64decode(encoded)
                                ctx.frame_updated_at[direction] = time.monotonic() - (lane.get("frameAgeMs") or 0) / 1000
                            else:
                                ctx.frame_buffer.pop(direction, None)
                    else:
                        ctx.remote_nodes = []
                        ctx.system_running = False
                        ctx.frame_buffer.clear()
            except asyncio.CancelledError:
                raise
            except Exception:
                self.is_connected = False
                ctx.remote_nodes = []
                ctx.system_running = False
                ctx.frame_buffer.clear()
            await asyncio.sleep(0.5)

    async def close(self):
        if self.pubsub:
            await self.pubsub.unsubscribe()
        if self.redis_client:
            await self.redis_client.aclose()
