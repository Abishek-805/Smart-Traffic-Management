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
            self.redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            self.is_connected = True
            logger.info(f"WebSocket Server connected to Redis at '{self.redis_url}'")
        except Exception as e:
            logger.warning(f"WebSocket Server Redis connection fallback (in-memory mode): {e}")
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
            await self.redis_client.publish(REDIS_CHANNELS["TELEMETRY"], envelope.model_dump_json())
        except Exception as e:
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
            logger.warning(f"Error publishing camera event to Redis: {e}")

    async def start_listener(self, command_callback=None):
        if not self.is_connected or not self.redis_client:
            return
        try:
            from shared.constants.protocol import REDIS_CHANNELS
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe(REDIS_CHANNELS["SYSTEM_COMMANDS"])
            logger.info("WebSocket Server subscribed to Redis channel: SYSTEM_COMMANDS")

            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        raw = json.loads(message["data"])
                        data = raw.get("data", {})
                        cmd = data.get("command")
                        if cmd and command_callback:
                            await command_callback(cmd, data.get("payload"))
                    except Exception as err:
                        logger.warning(f"Error parsing Redis command message: {err}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"Redis command listener loop exited: {e}")

    async def close(self):
        if self.pubsub:
            await self.pubsub.unsubscribe()
        if self.redis_client:
            await self.redis_client.close()
