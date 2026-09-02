"""Lifecycle shared by the combined app and the split WebSocket service."""
import asyncio
import copy
import time
from functools import partial
from contextlib import suppress
from fastapi import WebSocket
from core.application_context import ApplicationContext

DIRECTIONS = ("north", "east", "south", "west")


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
        lane.update(frameId=ctx.live_telemetry.get(direction, {}).get("frame_id"),
                    serverProcessingMs=ctx.live_telemetry.get(direction, {}).get("server_processing_ms"),
                    queueWaitMs=ctx.live_telemetry.get(direction, {}).get("queue_wait_ms"),
                    frameAgeMs=round(age, 1) if age is not None else None,
                    streamStatus="LIVE" if live else "STALE" if session and seen else "CONNECTING" if session else "OFFLINE",
                    fps=ctx.live_telemetry.get(direction, {}).get("fps", 0) if live else 0,
                    inferenceTimeMs=ctx.live_telemetry.get(direction, {}).get("latency_metrics", {}).get("yolo_ms", 0))
    live_lanes = [v for v in lanes.values() if v["streamStatus"] == "LIVE"]
    payload.update(
        systemRunning=ctx.system_running, streamStatus="LIVE" if live_lanes else "STALE",
        pipelineHealthy=bool(ctx.system_running and live_lanes),
        stageCounters=ctx.get_stage_counters(), processingErrors=ctx.frame_processing_errors,
        frameAgeMs=round((now - ctx.last_frame_monotonic) * 1000, 1) if ctx.frame_updated_at else 0,
        totalVehicles=sum(v.get("vehicles", 0) for v in live_lanes),
        queueLength=sum(v.get("queue", 0) for v in live_lanes),
        capabilities={"emergencyDetection": False, "reinforcementLearning": False, "hardware": "SIMULATION"},
    )
    active_missing = payload.get("activePhase", "None").lower() not in {d for d, v in lanes.items() if v["streamStatus"] == "LIVE"}
    if not ctx.system_running or not live_lanes or active_missing:
        payload.update(activePhase="None", timeRemaining=0, greenDuration=0, signalState="ALL_RED",
                       phaseReason="System paused" if not ctx.system_running else "Waiting for fresh camera frames" if not live_lanes else "Selected approach unavailable; awaiting safe phase transition")
    payload.setdefault("activePhase", "None")
    payload.setdefault("greenDuration", 0)
    payload.setdefault("timeRemaining", 0)
    payload["nodes"] = [{
        "node_id": session.node_id, "camera_direction": session.camera_direction,
        "assigned_lane": session.camera_direction.capitalize() + " Approach",
        "device_name": "Mobile camera", "status": "CONNECTED",
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
    from ai.controller.control_manager import ControlManager
    loop = asyncio.get_running_loop()
    message_handler.ensure_frame_executor()
    ctx.pipeline = await loop.run_in_executor(
        message_handler.frame_executor, partial(TrafficPipeline, save_output=False, headless=True))
    ctx.control_manager = ControlManager(simulation_mode=True, headless=True)

    async def ticker():
        while True:
            try:
                for node_id in ctx.session_manager.get_expired_sessions():
                    ctx.session_manager.remove_session(node_id)
                    await ctx.connection_manager.disconnect(node_id)
                if ctx.system_running and ctx.pipeline.active_decision:
                    result = await loop.run_in_executor(message_handler.frame_executor, ctx.pipeline.process_step, {})
                    await loop.run_in_executor(message_handler.frame_executor, ctx.control_manager.process_result, result)
                    if ctx.latest_snapshot:
                        apply_signal(ctx.latest_snapshot["payload"], result)
                snapshot = runtime_snapshot(ctx)
                # One immutable snapshot, one writer per browser, no per-frame broadcast fanout.
                ctx.latest_snapshot = snapshot
                if publish:
                    await publish(snapshot)
            except asyncio.CancelledError:
                raise
            except Exception:
                ctx.frame_processing_errors += 1
            await asyncio.sleep(0.5)
    ctx.on_snapshot_updated = None
    return asyncio.create_task(ticker())


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

