"""
Master Single Unified FastAPI Web Application for Smart Traffic Management System.
Serves HTML Control Center pages, REST APIs, Mobile Camera WebSockets (/ws/camera),
and Browser Telemetry WebSockets (/ws/telemetry).
"""

import asyncio
from pathlib import Path
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from web.routes import dashboard_router, api_router
from server.websocket_server import camera_websocket_endpoint
import server.websocket_server as _ws_server
from ai.utils.logger import get_logger

logger = get_logger("ControlCenterApp")

from contextlib import asynccontextmanager
from core.application_context import ApplicationContext

# Paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan manager executing startup resource initialization and shutdown teardown.
    """
    logger.info("Starting Smart Traffic Control Center Web Application...")
    ctx = ApplicationContext.get_instance()

    # Patch the WebSocket server's MessageHandler to share the same session/connection
    # managers as the REST API — fixes the session isolation bug without circular imports.
    _ws_server.message_handler.session_manager = ctx.session_manager
    _ws_server.message_handler.connection_manager = ctx.connection_manager
    logger.info("WebSocket MessageHandler wired to shared ApplicationContext managers.")

    # Initialize TrafficPipeline and ControlManager singletons in ApplicationContext
    if ctx.pipeline is None:
        from ai.pipeline.traffic_pipeline import TrafficPipeline
        ctx.pipeline = TrafficPipeline(save_output=False)
    if ctx.control_manager is None:
        from ai.controller.control_manager import ControlManager
        ctx.control_manager = ControlManager(simulation_mode=True)
    logger.info("TrafficPipeline and ControlManager initialized in ApplicationContext.")

    import time
    async def broadcast_telemetry(snapshot_data: dict):
        """Broadcast the telemetry snapshot to all connected browser clients instantly."""
        if not telemetry_clients:
            return
        now_ms = int(time.time() * 1000)
        payload_copy = dict(snapshot_data.get("payload", {}))
        payload_copy["broadcastTimestamp"] = now_ms
        
        # Calculate pipeline latency if captureTimestamp exists
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
            if ws in telemetry_clients:
                telemetry_clients.remove(ws)

    ctx.on_snapshot_updated = broadcast_telemetry

    # Background periodic session sweeper task
    async def _session_sweeper():
        while ctx.system_running:
            await asyncio.sleep(15.0)
            try:
                expired = ctx.session_manager.cleanup_expired_sessions()
                if expired:
                    logger.info(f"Cleaned up {len(expired)} expired camera session(s): {expired}")
            except Exception as e:
                logger.warning(f"Error in session sweeper: {e}")

    sweeper_task = asyncio.create_task(_session_sweeper())

    yield
    logger.info("Shutting down Smart Traffic Control Center Web Application...")
    ctx.system_running = False
    sweeper_task.cancel()
    if ctx.pipeline:
        ctx.pipeline.release()
    if ctx.control_manager:
        ctx.control_manager.release()


# Single Unified FastAPI Instance
app = FastAPI(
    title="Smart Traffic Management System — Control Center",
    description="Production Web Control Center for real-time AI adaptive traffic signal controller.",
    version="2.0.0",
    lifespan=lifespan,
)

# Mount Static Assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include Routers — canonical API at /api/v1
app.include_router(dashboard_router)
app.include_router(api_router)

# Legacy compatibility: redirect /api/* → /api/v1/* (308 Permanent Redirect)
from fastapi import Request
from fastapi.responses import RedirectResponse

@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def legacy_api_redirect(path: str, request: Request):
    """Redirect legacy /api/* callers to the canonical /api/v1/* endpoint."""
    canonical_url = f"/api/v1/{path}"
    if request.url.query:
        canonical_url += f"?{request.url.query}"
    return RedirectResponse(url=canonical_url, status_code=308)

# Mount Camera Node WebSocket Endpoint (/ws/camera)
app.add_api_websocket_route("/ws/camera", camera_websocket_endpoint)

# --- Browser Live Telemetry WebSockets (/ws/telemetry) ---
telemetry_clients: Set[WebSocket] = set()


@app.websocket("/ws/telemetry")
async def telemetry_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live browser control room telemetry updates broadcasting immutable PipelineStateSnapshots with stream health metadata."""
    await websocket.accept()
    telemetry_clients.add(websocket)
    logger.info(f"Browser telemetry WebSocket connected: {websocket.client}")

    try:
        phases = ["North", "East", "South", "West"]
        idx = 0
        tick = 20
        import time
        while True:
            await asyncio.sleep(1.0)
            ctx = ApplicationContext.get_instance()
            now_mono = time.monotonic()
            now_wall = time.time()
            frame_age_sec = round(now_mono - ctx.last_frame_monotonic, 2)
            frame_age_ms = round(frame_age_sec * 1000.0, 1)
            is_stalled = frame_age_sec > 2.5
            is_healthy = (ctx.frame_processing_errors == 0) and not is_stalled

            # Log status transition events
            if is_stalled != ctx.is_pipeline_stalled:
                ctx.is_pipeline_stalled = is_stalled
                logger.info(f"[TELEMETRY STATE EVENT] pipeline_stalled={is_stalled} | frame_age_sec={frame_age_sec}s | status={'STALE' if is_stalled else 'LIVE'}")

            stream_status = "LIVE" if not is_stalled else "STALE"

            if ctx.latest_snapshot:
                # Inject operational stream health indicators into latest snapshot copy
                snapshot_data = dict(ctx.latest_snapshot)
                payload_copy = dict(snapshot_data.get("payload", {}))
                payload_copy.update({
                    "snapshotTimestamp": now_wall,
                    "lastFrameTimestamp": now_wall - frame_age_sec,
                    "frameAgeMs": frame_age_ms,
                    "pipelineHealthy": is_healthy,
                    "pipelineStalled": is_stalled,
                    "streamStatus": stream_status,
                    "processingErrors": ctx.frame_processing_errors,
                })
                snapshot_data["payload"] = payload_copy
                await websocket.send_json(snapshot_data)
            else:
                # Build default per-lane metrics from context history or zeros
                lanes_payload = {}
                for d_name in ["north", "south", "east", "west"]:
                    l_stat = ctx.lane_stats_history.get(d_name)
                    if l_stat:
                        v_cnt = int(getattr(l_stat, "live_count", 0))
                        q_val = float(getattr(l_stat, "total_queue_time_sec", 0.0))
                        p_score = float(getattr(l_stat, "pce_score", 0.0))
                        den = str(getattr(l_stat, "density", "LOW"))
                        prio = round(v_cnt * 0.5 + p_score * 0.5, 2)
                        lanes_payload[d_name] = {
                            "vehicles": v_cnt,
                            "queue": round(q_val, 1),
                            "wait": round(q_val, 1),
                            "pce": round(p_score, 1),
                            "density": den,
                            "priority": prio,
                        }
                    else:
                        lanes_payload[d_name] = {
                            "vehicles": 0,
                            "queue": 0.0,
                            "wait": 0.0,
                            "pce": 0.0,
                            "density": "LOW",
                            "priority": 0.0,
                        }

                tot_veh = sum(l["vehicles"] for l in lanes_payload.values())
                tot_q = round(sum(l["queue"] for l in lanes_payload.values()), 1)
                tot_pce = round(sum(l["pce"] for l in lanes_payload.values()), 1)

                tick -= 1
                if tick <= 0:
                    idx = (idx + 1) % len(phases)
                    tick = 25
                payload = {
                    "protocol": "1.0",
                    "type": "SystemStatusUpdated",
                    "timestamp": now_wall,
                    "payload": {
                        "activePhase": phases[idx],
                        "greenDuration": 25,
                        "timeRemaining": tick,
                        "totalVehicles": tot_veh,
                        "queueLength": tot_q,
                        "pceScore": tot_pce,
                        "operatingMode": "AUTOMATIC",
                        "snapshotTimestamp": now_wall,
                        "lastFrameTimestamp": now_wall,
                        "frameAgeMs": frame_age_ms,
                        "pipelineHealthy": is_healthy,
                        "pipelineStalled": is_stalled,
                        "streamStatus": stream_status if frame_age_sec > 5.0 else "CONNECTING",
                        "processingErrors": 0,
                        "lanes": lanes_payload,
                    },
                }
                await websocket.send_json(payload)
    except WebSocketDisconnect:
        telemetry_clients.discard(websocket)
        logger.info(f"Browser telemetry WebSocket disconnected: {websocket.client}")
    except Exception as e:
        logger.exception(f"Exception in telemetry websocket endpoint: {e}")
        telemetry_clients.discard(websocket)


def get_app() -> FastAPI:
    """Return unified FastAPI application."""
    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.app:app", host="0.0.0.0", port=8000, reload=True)
