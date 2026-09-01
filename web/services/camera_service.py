"""Camera configuration and fresh annotated MJPEG previews."""
import asyncio
import time
from fastapi import HTTPException
from core.application_context import ApplicationContext

DIRECTIONS = ("north", "south", "east", "west")

class CameraService:
    def __init__(self, ctx=None):
        self.ctx = ctx or ApplicationContext.get_instance()

    def get_camera_configs(self):
        from web.services.node_service import NodeService
        nodes = NodeService(self.ctx).get_connected_nodes()["nodes"]
        payload = (self.ctx.latest_snapshot or {}).get("payload", {})
        streams = {}
        for direction in DIRECTIONS:
            node = next((n for n in nodes if n.get("assigned_lane", "").lower().startswith(direction)), {})
            lane = payload.get("lanes", {}).get(direction, {})
            streams[direction] = {
                "source": f"/api/v1/cameras/{direction}/feed",
                "status": node.get("status", "OFFLINE"),
                "fps": lane.get("fps", 0), "latency_ms": lane.get("inferenceTimeMs"),
            }
        return {"mode": "mobile", "streams": streams}

    async def generate_mjpeg_stream(self, direction):
        direction = direction.lower()
        if direction not in DIRECTIONS:
            raise HTTPException(422, "Invalid camera direction")
        previous = None
        while self.ctx.system_running:
            seen = self.ctx.frame_updated_at.get(direction)
            live = self.ctx.frame_buffer.get(direction)
            if not live or seen is None or time.monotonic() - seen > 3:
                return  # End stale feeds rather than showing an old frame as live.
            if live is not previous:
                frame_id = self.ctx.live_telemetry.get(direction, {}).get("frame_id", "")
                header = f"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: {len(live)}\r\nX-Frame-Id: {frame_id}\r\nCache-Control: no-store\r\n\r\n"
                yield header.encode() + live + b"\r\n"
                previous = live
            await asyncio.sleep(0.1)

