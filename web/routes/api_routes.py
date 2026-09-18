"""Canonical REST routes shared by the combined and split deployments."""
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from core.application_context import ApplicationContext
from web.schemas import ApiResponse, SystemVersionInfo, SystemHealthData, MobileNodesData, MobileNodeItem, NodeHealthSummary, LogsResponseData, LogEntryItem
from web.services.system_service import SystemService
from web.services.camera_service import CameraService
from web.services.node_service import NodeService
from web.services.log_service import LogService
from ai.pipeline.digital_intersection import DigitalIntersection

router = APIRouter(prefix="/api/v1", tags=["REST API v1"])
system_svc, camera_svc, node_svc, log_svc = SystemService(), CameraService(), NodeService(), LogService()
digital_intersection = DigitalIntersection()


def wrap_response(data):
    return {"success": True, "timestamp": datetime.now(timezone.utc).isoformat(), "data": data}


def direction_value(direction):
    direction = direction.lower()
    if direction not in ("north", "south", "east", "west"):
        raise HTTPException(422, "Choose north, south, east or west")
    return direction


import hmac
import logging

logger = logging.getLogger("web.routes.api_routes")


class OperatorAuthManager:
    """Manages configurable operator authentication state, startup checks, and token verification."""

    def __init__(self):
        self._warned = False

    def validate_startup_configuration(self) -> None:
        """Enforce that OPERATOR_AUTH_MODE=required has a valid key configured on startup."""
        mode = os.getenv("OPERATOR_AUTH_MODE", "optional").strip().lower()
        key = os.getenv("OPERATOR_API_KEY", "").strip()
        if mode == "required" and not key:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: OPERATOR_AUTH_MODE is set to 'required', "
                "but OPERATOR_API_KEY is empty or unset. System will refuse to start without a valid operator secret."
            )
        if mode != "required" and not self._warned:
            logger.warning(
                "[SECURITY NOTICE] OPERATOR AUTHENTICATION IS DISABLED (MODE=OPTIONAL). "
                "Operator control endpoints are accepting unauthenticated requests. "
                "This mode is intended strictly for trusted/demo local LAN environments. "
                "Production municipal and public deployments MUST configure OPERATOR_AUTH_MODE=required "
                "and set a strong OPERATOR_API_KEY."
            )
            self._warned = True

    def verify(self, token: Optional[str]) -> bool:
        """Verify operator credentials using constant-time comparison without logging secrets."""
        mode = os.getenv("OPERATOR_AUTH_MODE", "optional").strip().lower()
        key = os.getenv("OPERATOR_API_KEY", "").strip()

        if mode == "required":
            if not key:
                logger.error("[SECURITY ERROR] OPERATOR_AUTH_MODE=required but OPERATOR_API_KEY is unset")
                raise HTTPException(500, "Server security misconfiguration: OPERATOR_API_KEY required")
            if not token or not token.strip() or not hmac.compare_digest(token.strip().encode("utf-8"), key.encode("utf-8")):
                raise HTTPException(401, "Unauthorized: invalid or missing operator API key")
            return True

        # Mode is optional
        if key and token:
            if not hmac.compare_digest(token.strip().encode("utf-8"), key.encode("utf-8")):
                raise HTTPException(401, "Unauthorized: invalid operator API key")
            return True

        if not self._warned:
            logger.warning(
                "[SECURITY NOTICE] Operator endpoint accessed without authentication in optional mode. "
                "Intended for trusted/demo LAN use. Configure OPERATOR_AUTH_MODE=required for production."
            )
            self._warned = True
        return True


auth_manager = OperatorAuthManager()


def verify_operator_auth(x_operator_token: Optional[str] = Header(None, alias="X-Operator-Token")) -> bool:
    return auth_manager.verify(x_operator_token)


async def command(name, payload=None):
    ctx = ApplicationContext.get_instance()
    from server.runtime import handle_command
    handler = ctx.command_handler or (None if ctx.remote_runtime else handle_command)
    if not handler:
        raise HTTPException(503, "Camera runtime is unavailable")
    try:
        result = await handler(name, payload or {})
        log_svc.add_log("INFO", "SYSTEM", "Runtime", result["message"])
        return wrap_response(result)
    except Exception as exc:
        raise HTTPException(503, str(exc)) from exc


@router.get("/version", response_model=ApiResponse[SystemVersionInfo])
async def get_version():
    return wrap_response(SystemVersionInfo(version="2.0.0"))


@router.get("/build")
async def get_build_info():
    return wrap_response({"version": "2.0.0", "backend": "FastAPI", "protocol": "1.0", "frontend": "React"})


@router.get("/system/health", response_model=ApiResponse[SystemHealthData])
async def get_system_health():
    raw = system_svc.get_health()
    ctx = ApplicationContext.get_instance()
    ready = time.monotonic() - ctx.remote_received_at < 3 if ctx.remote_runtime else ctx.pipeline is not None
    return wrap_response(SystemHealthData(
        system_status=raw["status"], operating_mode=raw["mode"], uptime_seconds=raw["uptime"],
        readiness=ready, cpu_percent=raw.get("cpu_percent"), memory_used_gb=raw.get("memory_used_gb"),
        memory_total_gb=raw.get("memory_total_gb"), frame_processing_errors=raw.get("frame_processing_errors", 0),
        inference_latency_ms=raw.get("inference_latency_ms"), stage_counters=raw.get("stage_counters", {}),
        components=raw["components"]))


@router.get("/system/status")
async def get_system_status():
    return wrap_response(system_svc.get_status())


@router.get("/system/digital-intersection")
async def get_digital_intersection():
    """Return complete digital intersection snapshot (4 approaches, phases, safety)."""
    snapshot = digital_intersection.get_snapshot()
    resp = wrap_response(snapshot)
    resp.update(snapshot)
    return resp


@router.get("/cameras")
async def get_cameras_config():
    return wrap_response(camera_svc.get_camera_configs())


@router.get("/cameras/{direction}/feed")
async def get_camera_mjpeg_feed(direction: str):
    return StreamingResponse(camera_svc.generate_mjpeg_stream(direction_value(direction)),
        media_type="multipart/x-mixed-replace; boundary=frame", headers={"Cache-Control": "no-store"})


@router.delete("/cameras/{direction}", dependencies=[Depends(verify_operator_auth)])
async def disconnect_camera(direction: str):
    return await command("DISCONNECT", {"direction": direction_value(direction)})


@router.post("/cameras/{direction}")
async def configure_camera(direction: str, payload: Dict[str, Any] = Body(...)):
    direction_value(direction)
    raise HTTPException(422, "This runtime accepts mobile cameras. Connect a phone using its direction QR code.")


@router.get("/mobile-nodes", response_model=ApiResponse[MobileNodesData])
async def get_mobile_nodes():
    raw_nodes = node_svc.get_connected_nodes()["nodes"]
    nodes = [MobileNodeItem(node_id=n["node_id"], name=n["device_name"], status=n["status"],
        fps=n.get("fps", 0), latency_ms=n.get("latency_ms"), battery_pct=n.get("battery_pct"),
        signal_dbm=n.get("signal_dbm"), last_seen=n["last_heartbeat"], assigned_lane=n["assigned_lane"],
        expires_at=n.get("expires_at")) for n in raw_nodes]
    connected = [n for n in nodes if n.status == "CONNECTED"]
    return wrap_response(MobileNodesData(nodes=nodes, summary=NodeHealthSummary(
        connected_nodes=len(connected), offline_nodes=sum(n.status == "OFFLINE" for n in nodes),
        average_fps=round(sum(n.fps for n in connected) / len(connected), 1) if connected else 0)))


@router.get("/analytics")
async def get_analytics_data():
    from web.services.analytics_service import AnalyticsService
    return wrap_response(AnalyticsService().get_analytics_summary())


@router.get("/logs", response_model=ApiResponse[LogsResponseData])
async def get_logs(category: Optional[str] = "ALL", level: Optional[str] = "ALL",
                   search: Optional[str] = None, limit: int = Query(100, ge=1, le=1000)):
    items = [LogEntryItem(**l) for l in log_svc.get_logs(category=category, level=level, search=search, limit=limit)]
    return wrap_response(LogsResponseData(total=len(items), logs=items))


@router.get("/qr/generate")
async def generate_qr_code(direction: str = "north"):
    return wrap_response(node_svc.generate_qr_payload_and_image(direction_value(direction)))


@router.post("/system/start", dependencies=[Depends(verify_operator_auth)])
async def start_system():
    return await command("START")


@router.post("/system/config", dependencies=[Depends(verify_operator_auth)])
async def configure_system(payload: Dict[str, Any] = Body(...)):
    try:
        confidence = float(payload["confidenceThreshold"])
        minimum, maximum = int(payload["minGreenTime"]), int(payload["maxGreenTime"])
        if not .05 <= confidence <= .95 or not 5 <= minimum <= maximum <= 120:
            raise ValueError()
    except (KeyError, ValueError, TypeError):
        raise HTTPException(422, "Confidence must be 0.05–0.95; green bounds must be 5 ≤ min ≤ max ≤ 120")
    return await command("CONFIGURE", payload)


@router.post("/system/stop", dependencies=[Depends(verify_operator_auth)])
async def stop_system():
    return await command("STOP")


@router.post("/system/restart", dependencies=[Depends(verify_operator_auth)])
async def restart_system():
    return await command("RESTART")
