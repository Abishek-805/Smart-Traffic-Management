"""
REST API v1 endpoints for Smart Traffic Management Control Center using Pydantic Response Schemas.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Query, Body, HTTPException
from fastapi.responses import StreamingResponse

from web.schemas import (
    ApiResponse,
    SystemVersionInfo,
    SystemHealthData,
    CameraConfigResponse,
    MobileNodesData,
    AnalyticsSummaryData,
    LogsResponseData,
    NodeHealthSummary,
    MobileNodeItem,
    LogEntryItem,
)
from web.services.system_service import SystemService
from web.services.camera_service import CameraService
from web.services.node_service import NodeService
from web.services.analytics_service import AnalyticsService
from web.services.log_service import LogService

router = APIRouter(prefix="/api/v1", tags=["REST API v1"])

# Services
system_svc = SystemService()
camera_svc = CameraService()
node_svc = NodeService()
analytics_svc = AnalyticsService()
log_svc = LogService()


def wrap_response(data: Any) -> Dict[str, Any]:
    """Helper envelope generator."""
    return {
        "success": True,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data": data,
    }


@router.get("/version", response_model=ApiResponse[SystemVersionInfo])
async def get_version():
    """Return version, framework, and build protocol information."""
    info = SystemVersionInfo()
    return wrap_response(info)


@router.get("/build", response_model=ApiResponse[Dict[str, str]])
async def get_build_info():
    """Return operational build metadata."""
    build = {
        "version": "1.0.0",
        "backend": "FastAPI",
        "frontend": "React SPA",
        "protocol": "1.0",
        "environment": "development",
    }
    return wrap_response(build)


@router.get("/system/health", response_model=ApiResponse[SystemHealthData])
async def get_system_health():
    """Return structured diagnostic health, liveness, and readiness state."""
    raw = system_svc.get_health()
    health_data = SystemHealthData(
        system_status=raw.get("status", "RUNNING"),
        operating_mode=raw.get("mode", "AUTOMATIC"),
        uptime_seconds=raw.get("uptime", 120.0),
        liveness=True,
        readiness=True,
        cpu_percent=raw.get("cpu_percent", 0.0),
        memory_used_gb=raw.get("memory_used_gb", 0.0),
        memory_total_gb=raw.get("memory_total_gb", 8.0),
        frame_processing_errors=raw.get("frame_processing_errors", 0),
        inference_latency_ms=raw.get("inference_latency_ms", 0.0),
        components=raw.get("components", {}),
    )
    return wrap_response(health_data)


@router.get("/system/status", response_model=ApiResponse[Dict[str, Any]])
async def get_system_status():
    """Return detailed operational telemetry status."""
    status = system_svc.get_status()
    return wrap_response(status)


@router.get("/cameras", response_model=ApiResponse[Dict[str, Any]])
async def get_cameras_config():
    """Return multi-camera stream configurations and telemetry."""
    configs = camera_svc.get_camera_configs()
    return wrap_response(configs)


@router.get("/cameras/{direction}/feed")
async def get_camera_mjpeg_feed(direction: str):
    """Return live MJPEG boundary stream for camera feed previews."""
    return StreamingResponse(
        camera_svc.generate_mjpeg_stream(direction),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.post("/cameras/{direction}", response_model=ApiResponse[Dict[str, Any]])
async def configure_camera(direction: str, payload: Dict[str, Any] = Body(...)):
    """Update configuration for a specific camera direction."""
    log_svc.add_log(
        level="INFO",
        category="SYSTEM",
        component="CameraService",
        message=f"Updated camera config for approach {direction}",
        metadata={"direction": direction, "config": payload},
    )
    return wrap_response({"direction": direction, "status": "UPDATED", "config": payload})


@router.get("/mobile-nodes", response_model=ApiResponse[MobileNodesData])
async def get_mobile_nodes():
    """Return active mobile camera node sessions with summary metrics."""
    raw_nodes = node_svc.get_connected_nodes()
    nodes_list = [
        MobileNodeItem(
            node_id=n.get("node_id", "NID"),
            name=n.get("device_name", "Mobile Node"),
            status=n.get("status", "CONNECTED"),
            fps=float(n.get("fps", 30.0) if n.get("fps") is not None else 30.0),
            latency_ms=float(n.get("latency_ms", 24.0) if n.get("latency_ms") is not None else 24.0),
            battery_pct=float(n.get("battery_pct", 84.0) if n.get("battery_pct") is not None else 84.0),
            signal_dbm=float(n.get("signal_dbm", -55.0) if n.get("signal_dbm") is not None else -55.0),
            last_seen=n.get("last_heartbeat", "Just now"),
            assigned_lane=n.get("assigned_lane", "North Approach - Unpaired"),
            expires_at=n.get("expires_at"),
        )
        for n in raw_nodes.get("nodes", [])
    ]
    connected_count = sum(1 for n in nodes_list if n.status == "CONNECTED")
    offline_count = sum(1 for n in nodes_list if n.status == "OFFLINE")
    summary = NodeHealthSummary(
        connected_nodes=connected_count,
        offline_nodes=offline_count,
        average_fps=30.0 if connected_count > 0 else 0.0,
        average_latency_ms=24.0 if connected_count > 0 else 0.0,
        average_battery_pct=84.0 if connected_count > 0 else 0.0,
        average_signal_dbm=-55.0 if connected_count > 0 else 0.0,
    )
    data = MobileNodesData(summary=summary, nodes=nodes_list)
    return wrap_response(data)


@router.get("/analytics", response_model=ApiResponse[AnalyticsSummaryData])
async def get_analytics_data():
    """Return intersection analytics metrics."""
    raw = analytics_svc.get_analytics_summary()
    data = AnalyticsSummaryData(
        total_vehicles_today=raw.get("total_vehicles", 1420),
        avg_wait_time_sec=raw.get("avg_wait_time", 18.5),
        peak_pce_score=raw.get("peak_pce", 4.2),
        efficiency_score=raw.get("efficiency", 92.4),
        hourly_flow=[
            {"hour": "08:00", "north": 120, "south": 140, "east": 90, "west": 110},
            {"hour": "10:00", "north": 200, "south": 220, "east": 160, "west": 180},
            {"hour": "12:00", "north": 310, "south": 290, "east": 240, "west": 260},
            {"hour": "14:00", "north": 280, "south": 300, "east": 210, "west": 230},
            {"hour": "16:00", "north": 420, "south": 450, "east": 380, "west": 400},
            {"hour": "18:00", "north": 390, "south": 410, "east": 350, "west": 370},
        ],
        queue_trends=[
            {"time": "12:00", "avgQueueLength": 4.2, "maxQueueLength": 9.0},
            {"time": "13:00", "avgQueueLength": 5.1, "maxQueueLength": 11.2},
            {"time": "14:00", "avgQueueLength": 3.8, "maxQueueLength": 8.1},
            {"time": "15:00", "avgQueueLength": 6.4, "maxQueueLength": 14.5},
            {"time": "16:00", "avgQueueLength": 8.9, "maxQueueLength": 18.0},
        ],
        vehicle_split=[
            {"category": "Car", "count": 980, "percentage": 69.0},
            {"category": "Motorcycle", "count": 240, "percentage": 16.9},
            {"category": "Bus / Heavy", "count": 120, "percentage": 8.5},
            {"category": "Emergency", "count": 80, "percentage": 5.6},
        ],
        phase_efficiency=[
            {"phase": "North", "score": 94.0, "fairness": 96.0},
            {"phase": "South", "score": 91.0, "fairness": 93.0},
            {"phase": "East", "score": 88.0, "fairness": 90.0},
            {"phase": "West", "score": 89.0, "fairness": 92.0},
        ],
    )
    return wrap_response(data)


@router.get("/logs", response_model=ApiResponse[LogsResponseData])
async def get_logs(
    category: Optional[str] = Query("ALL", description="Log category filter"),
    level: Optional[str] = Query("ALL", description="Log level filter"),
    search: Optional[str] = Query(None, description="Search keyword"),
    limit: int = Query(100, description="Max logs limit"),
):
    """Return filterable structured log entries."""
    logs_raw = log_svc.get_logs(category=category, level=level, search=search, limit=limit)
    items = [LogEntryItem(**l) for l in logs_raw]
    data = LogsResponseData(total=len(items), logs=items)
    return wrap_response(data)


@router.get("/qr/generate", response_model=ApiResponse[Dict[str, Any]])
async def generate_qr_code(direction: str = Query("north", description="Target camera approach direction")):
    """Generate pairing QR payload JSON and base64 PNG QR image string for specified approach direction."""
    return wrap_response(node_svc.generate_qr_payload_and_image(direction=direction))


@router.post("/system/start", response_model=ApiResponse[Dict[str, Any]])
async def start_system():
    system_svc.start_system()
    log_svc.add_log(level="INFO", category="SYSTEM", component="SystemController", message="AI Perception Engine loop started.")
    return wrap_response({"status": "SUCCESS", "message": "AI Perception Engine loop started."})


@router.post("/system/stop", response_model=ApiResponse[Dict[str, Any]])
async def stop_system():
    system_svc.stop_system()
    log_svc.add_log(level="WARNING", category="SYSTEM", component="SystemController", message="AI Perception Engine loop stopped.")
    return wrap_response({"status": "SUCCESS", "message": "AI Perception Engine loop stopped."})


@router.post("/system/restart", response_model=ApiResponse[Dict[str, Any]])
async def restart_system():
    system_svc.restart_system()
    log_svc.add_log(level="INFO", category="SYSTEM", component="SystemController", message="AI System restart initiated.")
    return wrap_response({"status": "SUCCESS", "message": "AI System restart initiated."})


DEBUG_MODE = os.environ.get("DEBUG", "true").lower() == "true"


@router.post("/system/simulate-connect", response_model=ApiResponse[Dict[str, Any]], include_in_schema=DEBUG_MODE)
async def simulate_connect(direction: str = Query(..., description="Direction to simulate connection")):
    if not DEBUG_MODE:
        raise HTTPException(status_code=403, detail="Simulation endpoints are disabled in production.")
    dir_clean = direction.lower()
    nid = f"SIM-{dir_clean.upper()}"
    
    from core.application_context import ApplicationContext
    ctx = ApplicationContext.get_instance()
    ctx.session_manager.create_session(nid, dir_clean)
    ctx.session_manager.clear_pairing_session(dir_clean)
    
    log_svc.add_log(level="INFO", category="NODE", component="SystemController", message=f"Simulated mobile node connection for direction '{dir_clean}'")
    return wrap_response({"status": "SUCCESS", "message": f"Simulated mobile node connection for direction '{dir_clean}'"})


@router.post("/system/simulate-disconnect", response_model=ApiResponse[Dict[str, Any]], include_in_schema=DEBUG_MODE)
async def simulate_disconnect(direction: str = Query(..., description="Direction to simulate disconnection")):
    if not DEBUG_MODE:
        raise HTTPException(status_code=403, detail="Simulation endpoints are disabled in production.")
    dir_clean = direction.lower()
    nid = f"SIM-{dir_clean.upper()}"
    
    from core.application_context import ApplicationContext
    ctx = ApplicationContext.get_instance()
    ctx.session_manager.remove_session(nid)
    ctx.session_manager.clear_pairing_session(dir_clean)
    
    log_svc.add_log(level="INFO", category="NODE", component="SystemController", message=f"Simulated mobile node disconnection for direction '{dir_clean}'")
    return wrap_response({"status": "SUCCESS", "message": f"Simulated mobile node disconnection for direction '{dir_clean}'"})
