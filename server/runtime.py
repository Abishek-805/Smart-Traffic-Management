"""Lifecycle shared by the combined app and the split WebSocket service."""
import asyncio
import copy
import time
from functools import partial
from contextlib import suppress
from fastapi import WebSocket
from core.application_context import ApplicationContext
from config.deployment import ACTIVE_PROFILE, DeploymentProfile
from ai.hardware import HardwareConnectionState, hardware_is_safe_to_run
from ai.utils.logger import get_logger

DIRECTIONS = ("north", "east", "south", "west")
logger = get_logger("Runtime")


def initialize_control_manager(
    ctx: ApplicationContext,
    profile: DeploymentProfile = ACTIVE_PROFILE,
):
    """Create the requested output mode and fail closed if hardware is unavailable."""
    from ai.controller.control_manager import ControlManager

    control = ControlManager(
        esp32_port=profile.serial_port,
        esp32_baudrate=profile.serial_baudrate,
        simulation_mode=profile.hardware_mode == "simulation",
        headless=True,
    )
    ctx.startup_config = profile
    ctx.control_manager = control
    if not hardware_is_safe_to_run(control.esp32_interface.get_status()):
        ctx.system_running = False
    return control


def _hardware_status(ctx: ApplicationContext) -> dict:
    if ctx.control_manager and getattr(ctx.control_manager, "esp32_interface", None):
        return ctx.control_manager.esp32_interface.get_status().to_dict()
    profile = ctx.startup_config or ACTIVE_PROFILE
    return {
        "connected": False,
        "simulation_mode": False,
        "port": profile.serial_port,
        "baudrate": profile.serial_baudrate,
        "connection_state": HardwareConnectionState.DISCONNECTED.value,
        "last_ack_time": None,
        "last_ack": None,
        "last_error": None,
        "total_commands_sent": 0,
    }


def runtime_snapshot(ctx):
    snapshot = copy.deepcopy(ctx.latest_snapshot or {"type": "SystemStatusUpdated", "payload": {}})
    payload = snapshot["payload"]
    now = time.monotonic()
    lanes = payload.setdefault("lanes", {})
    for direction in DIRECTIONS:
        lane = lanes.setdefault(direction, {"vehicles": 0, "queue": 0, "wait": 0, "pce": 0, "priority": 0, "density": "LOW"})
        seen = ctx.frame_updated_at.get(direction)
        age = (now - seen) * 1000 if seen else None
        session = ctx.session_manager.get_session_by_direction(direction)
        live = bool(ctx.system_running and session and age is not None and age < 3000)
        lane_telemetry = ctx.live_telemetry.get(direction, {})
        temporal = lane_telemetry.get("latency_metrics", {})
        lane.update(frameId=lane_telemetry.get("frame_id"),
                    latestFrameId=lane_telemetry.get("latest_frame_id"),
                    lastDetectionFrameId=lane_telemetry.get("last_detection_frame_id"),
                    lastPredictionFrameId=lane_telemetry.get("last_prediction_frame_id"),
                    lastTrackedFrameId=lane_telemetry.get("last_tracked_frame_id"),
                    detectorRan=lane_telemetry.get("detector_ran", False),
                    detectorFps=temporal.get("detector_fps"),
                    trackerFps=temporal.get("tracker_fps"),
                    trackingTimeMs=temporal.get("tracking_ms"),
                    serverProcessingMs=lane_telemetry.get("server_processing_ms"),
                    queueWaitMs=lane_telemetry.get("queue_wait_ms"),
                    frameAgeMs=round(age, 1) if age is not None else None,
                    streamStatus="LIVE" if live else "STALE" if session and seen else "CONNECTING" if session else "OFFLINE",
                    fps=lane_telemetry.get("fps", 0) if live else 0,
                    inferenceTimeMs=temporal.get("yolo_ms"))
    live_lanes = [v for v in lanes.values() if v["streamStatus"] == "LIVE"]
    hardware = _hardware_status(ctx)
    profile = ctx.startup_config or ACTIVE_PROFILE
    payload.update(
        systemRunning=ctx.system_running, streamStatus="LIVE" if live_lanes else "STALE",
        pipelineHealthy=bool(ctx.system_running and live_lanes),
        stageCounters=ctx.get_stage_counters(), processingErrors=ctx.frame_processing_errors,
        frameAgeMs=round((now - ctx.last_frame_monotonic) * 1000, 1) if ctx.frame_updated_at else None,
        totalVehicles=sum(v.get("vehicles", 0) for v in live_lanes),
        queueLength=sum(v.get("queue", 0) for v in live_lanes),
        capabilities={"emergencyDetection": False, "reinforcementLearning": False,
                      "hardware": hardware["connection_state"]},
        hardwareStatus=hardware,
        deploymentProfile=profile.to_telemetry(),
    )
    active_missing = payload.get("activePhase", "None").lower() not in {d for d, v in lanes.items() if v["streamStatus"] == "LIVE"}
    if not ctx.system_running or not live_lanes or active_missing:
        payload.update(activePhase="None", timeRemaining=0, greenDuration=0, signalState="ALL_RED",
                       phaseReason="System paused" if not ctx.system_running else "Waiting for fresh camera frames" if not live_lanes else "Selected approach unavailable; awaiting safe phase transition")
    payload.setdefault("activePhase", "None")
    payload.setdefault("greenDuration", 0)
    payload.setdefault("timeRemaining", 0)
    from server.camera_lifecycle import CameraStatusSnapshot

    def node_status(session):
        status = CameraStatusSnapshot.from_session(session)
        status.last_inference_at = ctx.frame_updated_at.get(session.camera_direction)
        return status.derive_state(now).value

    payload["nodes"] = [{
        "node_id": session.node_id, "camera_direction": session.camera_direction,
        "assigned_lane": session.camera_direction.capitalize() + " Approach",
        "device_name": "Mobile camera",
        "status": node_status(session),
        "last_heartbeat": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(session.last_heartbeat)),
        "fps": lanes[session.camera_direction]["fps"],
        "latency_ms": None, "battery_pct": None, "signal_dbm": None,
    } for session in ctx.session_manager.sessions.values() if not session.is_expired()]
    payload["healthComponents"] = ctx.get_health_dict()["components"]
    snapshot["timestamp"] = time.time()
    return snapshot


def apply_signal(payload, result):
    decision = result.signal_decision
    if not decision:
        return
    payload.update(activePhase=decision.green_lane.value,
                   greenDuration=decision.green_duration_sec,
                   timeRemaining=result.remaining_green_sec,
                   phaseReason=decision.reason_details,
                   signalState=result.signal_state)


async def handle_command(command, payload=None):
    ctx = ApplicationContext.get_instance()
    payload = payload or {}
    if command == "DISCONNECT":
        direction = payload.get("direction")
        session = ctx.session_manager.get_session_by_direction(direction)
        if session:
            ctx.session_manager.remove_session(session.node_id)
            await ctx.connection_manager.disconnect(session.node_id)
        ctx.frame_buffer.pop(direction, None)
        ctx.frame_updated_at.pop(direction, None)
        ctx.live_telemetry.pop(direction, None)
        return {"status": "SUCCESS", "message": "Camera disconnected"}
    if command == "CONFIGURE":
        confidence = float(payload["confidenceThreshold"])
        minimum, maximum = int(payload["minGreenTime"]), int(payload["maxGreenTime"])
        if not .05 <= confidence <= .95 or not 5 <= minimum <= maximum <= 120:
            raise ValueError("Confidence must be 0.05–0.95 and green durations 5 ≤ min ≤ max ≤ 120 seconds")
        if not ctx.pipeline:
            raise RuntimeError("AI runtime is not ready")
        def configure():
            with ctx.pipeline._lock:
                ctx.pipeline.model_manager.confidence = confidence
                ctx.pipeline.signal_scheduler.min_green_sec = minimum
                ctx.pipeline.signal_scheduler.max_green_sec = maximum
        await asyncio.to_thread(configure)
        return {"status": "SUCCESS", "message": "Confidence applied; timing bounds apply from the next phase"}
    if command not in ("START", "STOP", "RESTART"):
        raise ValueError("Unsupported command")
    if command in ("START", "RESTART") and ctx.control_manager:
        hardware_status = ctx.control_manager.esp32_interface.get_status()
        if not hardware_is_safe_to_run(hardware_status):
            ctx.system_running = False
            raise RuntimeError(
                f"Cannot start while requested ESP32 hardware is "
                f"{hardware_status.connection_state.value}: "
                f"{hardware_status.last_error or 'serial connection unavailable'}"
            )
    ctx.system_running = command != "STOP"
    if command in ("STOP", "RESTART") and ctx.pipeline:
        # Wait for current inference before changing phase state.
        def reset_phase():
            with ctx.pipeline._lock:
                ctx.pipeline.active_decision = None
                ctx.pipeline.active_hardware_cmd = None
        await asyncio.to_thread(reset_phase)
        ctx.frame_buffer.clear()
        ctx.frame_updated_at.clear()
    stream_type = "START_STREAM" if ctx.system_running else "STOP_STREAM"
    for session in ctx.session_manager.sessions.values():
        session.streaming = ctx.system_running
    await ctx.connection_manager.broadcast({"type": stream_type, "timestamp": time.time(), "payload": {}})
    return {"status": "SUCCESS", "message": f"System {command.lower()} acknowledged by runtime"}


async def start_runtime(message_handler, publish=None):
    ctx = ApplicationContext.get_instance()
    ctx.remote_runtime = False
    ctx.command_handler = handle_command
    message_handler.session_manager = ctx.session_manager
    message_handler.connection_manager = ctx.connection_manager
    from ai.pipeline.traffic_pipeline import TrafficPipeline
    loop = asyncio.get_running_loop()
    message_handler.ensure_frame_executor()
    ctx.pipeline = await loop.run_in_executor(
        message_handler.frame_executor, partial(TrafficPipeline, save_output=False, headless=True))
    initialize_control_manager(ctx)
    from server.local_sources import LocalCameraSources
    message_handler.local_sources = LocalCameraSources(message_handler)
    await message_handler.local_sources.start()

    async def ticker():
        while True:
            await run_runtime_iteration(ctx, message_handler, publish)
            await asyncio.sleep(0.5)
    ctx.on_snapshot_updated = None
    return asyncio.create_task(ticker())


async def run_runtime_iteration(ctx, message_handler, publish=None) -> bool:
    """Run one fault-contained maintenance/scheduler iteration."""
    try:
        for node_id in ctx.session_manager.get_expired_sessions():
            ctx.session_manager.remove_session(node_id)
            await ctx.connection_manager.disconnect(node_id)
        if ctx.system_running and ctx.pipeline and ctx.pipeline.active_decision:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                message_handler.frame_executor, ctx.pipeline.process_step, {}
            )
            await loop.run_in_executor(
                message_handler.frame_executor, ctx.control_manager.process_result, result
            )
            if ctx.latest_snapshot:
                apply_signal(ctx.latest_snapshot["payload"], result)
        snapshot = runtime_snapshot(ctx)
        ctx.latest_snapshot = snapshot
        if publish:
            await publish(snapshot)
        return True
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        ctx.frame_processing_errors += 1
        logger.error("Runtime ticker failed (%s): %s", type(exc).__name__, exc)
        logger.debug("Runtime ticker traceback", exc_info=True)
        if ctx.control_manager:
            status = ctx.control_manager.esp32_interface.get_status()
            if not hardware_is_safe_to_run(status):
                ctx.system_running = False
        return False


async def stop_runtime(task, message_handler):
    ctx = ApplicationContext.get_instance()
    ctx.system_running = False
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
    await message_handler.shutdown()
    for node_id in list(ctx.connection_manager.active_connections):
        await ctx.connection_manager.disconnect(node_id)
    if ctx.pipeline:
        await asyncio.to_thread(ctx.pipeline.release)
        ctx.pipeline = None
    if ctx.control_manager:
        ctx.control_manager.release()
        ctx.control_manager = None


async def telemetry_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ctx = ApplicationContext.get_instance()
    try:
        while True:
            await asyncio.wait_for(websocket.send_json(runtime_snapshot(ctx)), timeout=2)
            await asyncio.sleep(0.5)
    except Exception:
        with suppress(Exception):
            await websocket.close()

