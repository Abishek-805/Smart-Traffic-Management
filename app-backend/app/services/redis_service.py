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
            self.redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            self.is_connected = True
            logger.info(f"App Backend connected to Redis at '{self.redis_url}'")
        except Exception as e:
            logger.warning(f"App Backend Redis connection fallback (in-memory mode): {e}")
            self.is_connected = False

    async def publish_command(self, command: str, payload: Optional[Dict[str, Any]] = None):
        if not self.is_connected or not self.redis_client:
            logger.info(f"Simulated local command publish: '{command}'")
            return
        try:
            from shared.constants.protocol import REDIS_CHANNELS
            from shared.events.event_types import EventTypes
            from shared.schemas.events import RedisEventEnvelope
            
            envelope = RedisEventEnvelope(
                event=EventTypes.SYSTEM_COMMAND,
                data={"command": command, "payload": payload or {}}
            )
            await self.redis_client.publish(REDIS_CHANNELS["SYSTEM_COMMANDS"], envelope.model_dump_json())
        except Exception as e:
            logger.warning(f"Error publishing command to Redis: {e}")

    async def start_listener(self):
        if not self.is_connected or not self.redis_client:
            return
        try:
            from shared.constants.protocol import REDIS_CHANNELS
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe(REDIS_CHANNELS["TELEMETRY"], REDIS_CHANNELS["CAMERA_EVENTS"])
            logger.info("App Backend subscribed to Redis channels: TELEMETRY, CAMERA_EVENTS")

            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        raw = json.loads(message["data"])
                        event_name = raw.get("event")
                        data = raw.get("data", {})
                        if event_name == "system.telemetry.updated":
                            self.latest_telemetry = data
                        elif event_name == "camera.registered":
                            nid = data.get("node_id", "NID")
                            self.connected_nodes[nid] = data
                        elif event_name == "camera.disconnected":
                            nid = data.get("node_id", "NID")
                            self.connected_nodes.pop(nid, None)
                    except Exception as err:
                        logger.warning(f"Error parsing Redis PubSub message: {err}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"Redis listener loop exited: {e}")

    async def close(self):
        if self.pubsub:
            await self.pubsub.unsubscribe()
        if self.redis_client:
            await self.redis_client.close()
