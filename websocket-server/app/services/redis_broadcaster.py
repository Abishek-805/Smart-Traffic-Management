import asyncio
import json
from typing import Optional, Dict, Any
from ai.utils.logger import get_logger

logger = get_logger("WebSocketRedisBroadcaster")

class WebSocketRedisBroadcaster:
    """Redis Pub/Sub interface for WebSocket Server."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.pubsub = None
        self.is_connected = False

    async def connect(self):
        try:
            import redis.asyncio as aioredis
            if self.redis_client:
                await self.redis_client.aclose()
            self.redis_client = aioredis.from_url(self.redis_url, decode_responses=True, socket_connect_timeout=2, socket_timeout=2)
            await self.redis_client.ping()
            self.is_connected = True
            logger.info(f"WebSocket Server connected to Redis at '{self.redis_url}'")
        except Exception as e:
            logger.warning(f"WebSocket Server Redis unavailable; split-service commands and telemetry are unavailable: {e}")
            self.is_connected = False

    async def publish_telemetry(self, snapshot: Dict[str, Any]):
        if not self.is_connected or not self.redis_client:
            return
        try:
            from shared.constants.protocol import REDIS_CHANNELS
            from shared.events.event_types import EventTypes
            from shared.schemas.events import RedisEventEnvelope
            
            envelope = RedisEventEnvelope(
                event=EventTypes.TELEMETRY_UPDATED,
                data=snapshot
            )
            import base64
            from core.application_context import ApplicationContext
            ctx = ApplicationContext.get_instance()
            await self.redis_client.set("traffic:latest_snapshot", envelope.model_dump_json(), ex=5)
            for direction, frame in list(ctx.frame_buffer.items()):
                if direction != "active":
                    await self.redis_client.set("traffic:frame:" + direction, base64.b64encode(frame).decode(), ex=3)
            await self.redis_client.publish(REDIS_CHANNELS["TELEMETRY"], envelope.model_dump_json())
        except Exception as e:
            self.is_connected = False
            logger.warning(f"Error publishing telemetry to Redis: {e}")

    async def publish_camera_event(self, event_type: str, data: Dict[str, Any]):
        if not self.is_connected or not self.redis_client:
            return
        try:
            from shared.constants.protocol import REDIS_CHANNELS
            from shared.schemas.events import RedisEventEnvelope
            
            envelope = RedisEventEnvelope(event=event_type, data=data)
            await self.redis_client.publish(REDIS_CHANNELS["CAMERA_EVENTS"], envelope.model_dump_json())
        except Exception as e:
            self.is_connected = False
            logger.warning(f"Error publishing camera event to Redis: {e}")

    async def start_listener(self, command_callback=None):
        from shared.constants.protocol import REDIS_CHANNELS
        while True:
            try:
                if not self.is_connected:
                    await self.connect()
                if not self.is_connected:
                    await asyncio.sleep(2)
                    continue
                self.pubsub = self.redis_client.pubsub()
                await self.pubsub.subscribe(REDIS_CHANNELS["SYSTEM_COMMANDS"])
                while self.is_connected:
                    message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1)
                    if not message:
                        await asyncio.sleep(0.05)
                        continue
                    raw = json.loads(message["data"])
                    data = raw.get("data", {})
                    payload = data.get("payload") or {}
                    if data.get("command") and command_callback:
                        try:
                            result = await command_callback(data["command"], payload)
                        except Exception as exc:
                            result = {"status": "ERROR", "message": str(exc)}
                        request_id = payload.get("request_id")
                        if request_id:
                            await self.redis_client.set("traffic:command:" + request_id, json.dumps(result), ex=15)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.is_connected = False
                logger.warning(f"Redis command connection lost; retrying: {exc}")
                await asyncio.sleep(2)
            finally:
                if self.pubsub:
                    try:
                        await self.pubsub.aclose()
                    except Exception:
                        pass
                    self.pubsub = None

    async def close(self):
        self.is_connected = False
        if self.pubsub:
            await self.pubsub.aclose()
        if self.redis_client:
            await self.redis_client.aclose()
