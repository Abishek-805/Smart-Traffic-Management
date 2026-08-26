import asyncio
import time
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect
from core.application_context import ApplicationContext
from ai.utils.logger import get_logger

logger = get_logger("TelemetryWebSocketHandler")

telemetry_clients: Set[WebSocket] = set()

async def telemetry_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    telemetry_clients.add(websocket)
    logger.info(f"Browser telemetry WebSocket connected: {websocket.client}")

    try:
        phases = ["North", "East", "South", "West"]
        idx = 0
        tick = 20
        while True:
            await asyncio.sleep(1.0)
            ctx = ApplicationContext.get_instance()
            now_mono = time.monotonic()
            now_wall = time.time()
            frame_age_sec = round(now_mono - ctx.last_frame_monotonic, 2)
            frame_age_ms = round(frame_age_sec * 1000.0, 1)
            is_stalled = frame_age_sec > 2.5
            is_healthy = (ctx.frame_processing_errors == 0) and not is_stalled

            stream_status = "LIVE" if not is_stalled else "STALE"

            if ctx.latest_snapshot:
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
