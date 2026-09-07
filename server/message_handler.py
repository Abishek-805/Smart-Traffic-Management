"""
MessageHandler parses incoming WebSocket JSON packets using Pydantic models,
delegates to SessionManager and ConnectionManager, and generates response payloads.
"""

import asyncio
import math
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from fastapi import WebSocket

from server.config import PROTOCOL_VERSION
from server.protocol import (
    MessageType,
    RegistrationMessage,
    RegistrationAckMessage,
    RegistrationAckPayload,
    HeartbeatMessage,
    HeartbeatAckMessage,
    HeartbeatAckPayload,
    DisconnectMessage,
    ErrorMessage,
    ErrorPayload,
)
from server.session_manager import SessionManager
from server.connection_manager import ConnectionManager
from ai.utils.logger import get_logger

logger = get_logger("MessageHandler")
_frame_worker_lock = threading.Lock()


class MessageHandler:
    """
    Handles parsing and processing of incoming WebSocket messages (REGISTER_CAMERA, HEARTBEAT, DISCONNECT).
    """

    def __init__(
        self,
        session_manager: Optional[SessionManager] = None,
        connection_manager: Optional[ConnectionManager] = None,
    ):
        self.session_manager = session_manager if session_manager else SessionManager()
        self.connection_manager = connection_manager if connection_manager else ConnectionManager()
        self._in_flight_directions = set()
        # Perception is serialized already; one long-lived worker keeps native
        # OpenCV/PyTorch workspaces on one thread instead of multiplying them
        # across asyncio's large default pool.
        self.frame_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="traffic-pipeline")

    def ensure_frame_executor(self) -> None:
        """Recreate the bounded worker when an app lifespan is started again."""
        if getattr(self.frame_executor, "_shutdown", False):
            self.frame_executor = ThreadPoolExecutor(
                max_workers=1, thread_name_prefix="traffic-pipeline"
            )

    async def process_message(self, raw_json: Dict[str, Any], websocket: WebSocket) -> Optional[Dict[str, Any]]:
        """
        Process an incoming JSON payload over WebSocket and return the response dict to transmit.
        """
        if not isinstance(raw_json, dict):
            return self._build_error("MALFORMED_JSON", "Payload must be a JSON object.")

        msg_type_str = raw_json.get("message_type") or raw_json.get("type")
        proto_ver = raw_json.get("protocol_version", PROTOCOL_VERSION)
        correlation_id = raw_json.get("id")

        if not msg_type_str:
            return self._build_error("MISSING_MESSAGE_TYPE", "Field 'message_type' or 'type' is required.")

        # Validate protocol version â€” reject mismatched clients with a clear error
        if proto_ver != PROTOCOL_VERSION:
            logger.warning(f"Protocol version mismatch: client={proto_ver!r}, server={PROTOCOL_VERSION!r}")
            err = self._build_error(
                "PROTOCOL_VERSION_MISMATCH",
                f"Server requires protocol version '{PROTOCOL_VERSION}', received '{proto_ver}'.",
            )
            err["id"] = correlation_id
            return err

        # Normalize message_type key
        raw_json["message_type"] = msg_type_str
        raw_json["type"] = msg_type_str

        try:
            msg_type = MessageType(msg_type_str)
        except ValueError:
            err = self._build_error("UNKNOWN_MESSAGE_TYPE", f"Unknown message type '{msg_type_str}'.")
            err["id"] = correlation_id
            return err

        if msg_type != MessageType.REGISTER_CAMERA:
            payload = raw_json.get("payload", {})
            if not isinstance(payload, dict):
                return self._build_error("INVALID_PAYLOAD", "payload must be an object")
            node_id = payload.get("node_id") or payload.get("cameraId")
            token = payload.get("session_token") or raw_json.get("token")
            if (not self.session_manager.validate_session(node_id, token)
                    or self.connection_manager.get_connection(node_id) is not websocket):
                return self._build_error("UNAUTHORIZED_SESSION", "Register this connection first")
            session = self.session_manager.get_session(node_id)
            direction = payload.get("direction") or payload.get("camera_direction")
            if direction and direction.lower() != session.camera_direction:
                return self._build_error("DIRECTION_MISMATCH", "Frame direction does not match registration")
            payload["direction"] = session.camera_direction
            if msg_type in (MessageType.START_STREAM, MessageType.STOP_STREAM):
                from core.application_context import ApplicationContext
                if msg_type == MessageType.START_STREAM and not ApplicationContext.get_instance().system_running:
                    return self._build_error("SYSTEM_PAUSED", "Start the system from the dashboard first")
                session.streaming = msg_type == MessageType.START_STREAM
                return {"type": msg_type.value, "timestamp": time.time(), "payload": {}, "id": correlation_id}
            if msg_type == MessageType.VIDEO_FRAME and not getattr(session, "streaming", True):
                return self._build_error("STREAM_PAUSED", "Request START_STREAM first")

        # Route message based on type
        if msg_type == MessageType.REGISTER_CAMERA:
            response = await self._handle_register_camera(raw_json, websocket)
        elif msg_type == MessageType.HEARTBEAT:
            response = await self._handle_heartbeat(raw_json)
        elif msg_type == MessageType.VIDEO_FRAME:
            response = await self._handle_video_frame(raw_json)
        elif msg_type == MessageType.DISCONNECT:
            return await self._handle_disconnect(raw_json)
        else:
            response = self._build_error("UNSUPPORTED_ACTION", f"Action '{msg_type_str}' is not supported.")

        # Echo the incoming correlation id so clients can unblock awaiting ACK
        if response is not None and correlation_id is not None:
            response["id"] = correlation_id
        return response

    async def _handle_register_camera(self, raw_json: dict, websocket: WebSocket) -> dict:
        """Handle REGISTER_CAMERA message and return REGISTRATION_ACK response."""
        payload_raw = raw_json.get("payload", {})
        if not isinstance(payload_raw, dict):
            payload_raw = {}

        node_id = (
            payload_raw.get("node_id")
            or payload_raw.get("session")
            or payload_raw.get("cameraId")
            or raw_json.get("token")
            or "CAM-001"
        )
        direction = payload_raw.get("camera_direction") or payload_raw.get("assignedLane")
        if not direction:
            # Extract direction from session ID string (e.g. CAM-SOUTH-PAIR -> south)
            node_id_upper = str(node_id).upper()
            for d in ["NORTH", "SOUTH", "EAST", "WEST"]:
                if d in node_id_upper:
                    direction = d.lower()
                    break
        if not direction:
            direction = "north"

        direction = str(direction).lower()
        if direction not in ("north", "south", "east", "west"):
            return self._build_error("INVALID_DIRECTION", "Choose north, south, east or west")
        registration_token = str(raw_json.get("token") or "")
        existing_node_session = self.session_manager.get_session(str(node_id))
        is_reconnect = bool(
            existing_node_session
            and existing_node_session.camera_direction == direction
            and existing_node_session.session_token == registration_token
            and not existing_node_session.is_expired()
        )
        is_pairing_authorized = self.session_manager.validate_pairing_session(
            direction, str(node_id), registration_token
        )
        if not is_pairing_authorized and not is_reconnect:
            return self._build_error(
                "UNAUTHORIZED_PAIRING",
                "Pairing QR is invalid, expired, or belongs to another direction",
            )
        previous = self.session_manager.get_session_by_direction(direction)
        if previous and previous.node_id != node_id:
            return self._build_error("DIRECTION_OCCUPIED", "Disconnect the existing camera for this direction first")
        payload_raw["node_id"] = node_id
        payload_raw["camera_direction"] = direction
        raw_json["payload"] = payload_raw

        try:
            msg = RegistrationMessage.model_validate(raw_json)
        except Exception as e:
            return self._build_error("INVALID_REGISTRATION_PAYLOAD", f"Schema validation error: {e}")

        payload = msg.payload
        await self.connection_manager.connect(node_id, websocket)
        session = self.session_manager.create_session(node_id, direction)
        if is_pairing_authorized:
            self.session_manager.clear_pairing_session(direction)

        ack = RegistrationAckMessage(
            type=MessageType.REGISTRATION_ACK,
            message_type=MessageType.REGISTRATION_ACK,
            payload=RegistrationAckPayload(
                node_id=node_id,
                session_token=session.session_token,
                status="CONNECTED",
                assigned_direction=direction,
                assignedLane=f"{direction.capitalize()} Intersection - Lane 1",
                cameraId=node_id,
                message="Camera registration successful",
            ),
        )
        d = ack.model_dump()
        d["type"] = "REGISTRATION_ACK"
        logger.info(f"[PAIRING] REGISTER â†’ ACK | node={node_id} | direction={direction} | token={session.session_token[:8]}...")

        # Schedule single authoritative START_STREAM signal to camera node so mobile app switches to STREAMING state
        async def _send_start_stream():
            await asyncio.sleep(0.1)
            if not hasattr(self, "start_stream_counts"):
                self.start_stream_counts = {}
            self.start_stream_counts[node_id] = self.start_stream_counts.get(node_id, 0) + 1
            count = self.start_stream_counts[node_id]

            from core.application_context import ApplicationContext
            if not ApplicationContext.get_instance().system_running or self.connection_manager.get_connection(node_id) is not websocket:
                return
            start_msg = {
                "type": "START_STREAM",
                "message_type": "START_STREAM",
                "timestamp": time.time(),
                "payload": {
                    "target_fps": 2,
                    "resolution": "1280 max edge",
                    "quality": 75,
                    "session_start_count": count,
                },
            }
            await self.connection_manager.send_to_node(node_id, start_msg)
            logger.info(f"[PAIRING] START_STREAM_SENT | node_id='{node_id}' | session_count={count} | assert_single_owner={count == 1}")

        asyncio.create_task(_send_start_stream())
        return d

    async def _handle_heartbeat(self, raw_json: dict) -> dict:
        """Handle HEARTBEAT message and return HEARTBEAT_ACK or ERROR."""
        payload_raw = raw_json.get("payload", {})
        if not isinstance(payload_raw, dict):
            payload_raw = {}

        node_id = (
            payload_raw.get("node_id")
            or payload_raw.get("cameraId")
            or "CAM-001"
        )
        token = (
            payload_raw.get("session_token")
            or raw_json.get("token")
            or ""
        )

        payload_raw["node_id"] = node_id
        payload_raw["session_token"] = token
        raw_json["payload"] = payload_raw

        try:
            msg = HeartbeatMessage.model_validate(raw_json)
        except Exception as e:
            return self._build_error("INVALID_HEARTBEAT_PAYLOAD", f"Schema validation error: {e}")

        payload = msg.payload
        valid = self.session_manager.update_heartbeat(node_id, token)

        if not valid:
            return self._build_error(
                "UNAUTHORIZED_SESSION",
                f"Session token invalid or expired for node '{node_id}'.",
                node_id=node_id,
            )

        ack = HeartbeatAckMessage(
            type=MessageType.HEARTBEAT_ACK,
            message_type=MessageType.HEARTBEAT_ACK,
            payload=HeartbeatAckPayload(
                node_id=node_id,
                status="OK",
            ),
        )
        d = ack.model_dump()
        d["type"] = "HEARTBEAT_ACK"
        d["payload"]["client_timestamp"] = raw_json.get("timestamp")
        logger.debug(f"[PAIRING] HEARTBEAT â†’ ACK | node={node_id}")
        return d

    async def _process_direction_loop(self, direction: str):
        """Worker task processing the latest queued frame for a specific lane direction."""
        logger.debug(f"[LATENCY-CONTROL] Starting frame processing loop for lane '{direction}'")
        while True:
            if hasattr(self, "latest_frames") and self.latest_frames:
                logger.debug(f"[LATENCY-CONTROL] worker loop for '{direction}' sees keys: {list(self.latest_frames.keys())}")
            raw_json = self.latest_frames.pop(direction, None) if hasattr(self, "latest_frames") else None
            if raw_json is None:
                event = self.frame_events.setdefault(direction, asyncio.Event())
                event.clear()
                await event.wait()
                continue

            try:
                payload_raw = raw_json.get("payload", {})
                frame_b64 = payload_raw.get("frame_data")
                frame_id = payload_raw.get("frame_id") or f"{direction.upper()}-000000"
                if frame_b64:
                    from core.application_context import ApplicationContext
                    ctx = ApplicationContext.get_instance()
                    if not ctx.system_running or time.time() * 1000 - raw_json["backend_receive_timestamp"] > 2500:
                        ctx.increment_stage_counter("dropped")
                        continue
                    ctx.last_backend_received_frame_id = frame_id
                    
                    # Read capture, upload, and receive times in milliseconds
                    cap_ts = payload_raw.get("capture_timestamp")
                    if not isinstance(cap_ts, (int, float)) or not math.isfinite(cap_ts):
                        source_ts = payload_raw.get("timestamp", time.time())
                        cap_ts = source_ts * 1000.0 if isinstance(source_ts, (int, float)) and math.isfinite(source_ts) else time.time() * 1000.0
                    upload_ts = payload_raw.get("upload_timestamp", cap_ts)
                    if not isinstance(upload_ts, (int, float)) or not math.isfinite(upload_ts):
                        upload_ts = cap_ts
                    rx_ts = raw_json.get("backend_receive_timestamp", time.time() * 1000.0)

                    res = await asyncio.get_running_loop().run_in_executor(
                        self.frame_executor, _process_frame_worker,
                        frame_b64, direction, cap_ts, upload_ts, rx_ts, frame_id)
                    logger.debug(f"[LATENCY-CONTROL] Background process worker finished for frame '{frame_id}'. res is None: {res is None}")
                    if res:
                        node_id = payload_raw.get("node_id")
                        token = payload_raw.get("session_token") or raw_json.get("token")
                        if not ctx.system_running or not self.session_manager.validate_session(node_id, token):
                            ctx.increment_stage_counter("dropped")
                            continue
                        dir_key, annotated_bytes, snapshot, telemetry = res
                        ctx.last_telemetry_frame_id = frame_id
                        logger.debug(f"[LATENCY-CONTROL] Updating snapshot in context for frame '{frame_id}'")
                        ctx.frame_buffer[dir_key] = annotated_bytes
                        ctx.frame_buffer["active"] = annotated_bytes
                        previous_seen = ctx.frame_updated_at.get(dir_key)
                        telemetry["fps"] = round(1 / max(0.001, time.monotonic() - previous_seen), 1) if previous_seen else 0
                        ctx.live_telemetry[dir_key] = telemetry
                        ctx.increment_stage_counter("processed")
                        ctx.last_frame_monotonic = time.monotonic()
                        ctx.frame_updated_at[dir_key] = time.monotonic()
                        await ctx.update_snapshot(snapshot)
                        await self.connection_manager.send_to_node(node_id, {
                            "type": "FRAME_ACK", "timestamp": time.time(), "payload": {
                                "frame_id": frame_id, "direction": dir_key,
                                "capture_timestamp": cap_ts,
                                "server_processing_ms": telemetry["server_processing_ms"],
                                "queue_wait_ms": telemetry["queue_wait_ms"],
                                "inference_ms": telemetry["latency_metrics"].get("yolo_ms", 0),
                                "vehicle_count": snapshot["payload"]["lanes"][dir_key]["vehicles"],
                            }})
                    else:
                        ctx.frame_processing_errors += 1
            except Exception as e:
                logger.warning(f"Error in background frame processing loop for '{direction}': {e}", exc_info=True)

    async def _handle_video_frame(self, raw_json: dict) -> Optional[dict]:
        """Handle incoming VIDEO_FRAME payload by offloading to the corresponding direction queue."""
        payload_raw = raw_json.get("payload", {})
        if isinstance(payload_raw, dict):
            frame_data = payload_raw.get("frame_data")
            if not isinstance(frame_data, str) or not frame_data or len(frame_data) > 2_000_000:
                return self._build_error("INVALID_FRAME", "JPEG base64 must be nonempty and below 2MB")
            direction = (
                payload_raw.get("direction")
                or payload_raw.get("camera_direction")
                or payload_raw.get("assigned_direction")
                or "north"
            ).lower()

            # Lazy initialize worker states
            if not hasattr(self, "latest_frames"):
                self.latest_frames = {}
                self.frame_events = {}
                self.dropped_frames_count = 0
                self.worker_tasks = {}

            # Log receive timestamp
            raw_json["backend_receive_timestamp"] = int(time.time() * 1000)

            from core.application_context import ApplicationContext
            ctx = ApplicationContext.get_instance()
            if not ctx.system_running:
                return self._build_error("SYSTEM_PAUSED", "System is paused")
            ctx.increment_stage_counter("received")

            # Latest Frame Wins Policy: check if there's already an unprocessed frame in the slot
            if direction in self.latest_frames:
                self.dropped_frames_count += 1
                ctx.increment_stage_counter("dropped")
                logger.debug(f"[LATENCY-CONTROL] Dropping stale frame for '{direction}' (Total dropped: {self.dropped_frames_count})")

            self.latest_frames[direction] = raw_json
            self.frame_events.setdefault(direction, asyncio.Event()).set()

            # Lazy start loop task
            if direction not in self.worker_tasks:
                self.worker_tasks[direction] = asyncio.create_task(self._process_direction_loop(direction))

        return None

    async def _handle_disconnect(self, raw_json: dict) -> Optional[dict]:
        """Handle DISCONNECT message and clean up node session & connection."""
        try:
            payload_raw = raw_json.get("payload", {})
            if isinstance(payload_raw, dict):
                node_id = payload_raw.get("node_id") or payload_raw.get("cameraId") or "CAM-001"
                token = payload_raw.get("session_token") or raw_json.get("token") or ""
                payload_raw["node_id"] = node_id
                payload_raw["session_token"] = token
                raw_json["payload"] = payload_raw

            msg = DisconnectMessage.model_validate(raw_json)
            payload = msg.payload
            node_id = payload.node_id
            if self.session_manager.validate_session(node_id, payload.session_token):
                self.session_manager.remove_session(node_id)
                await self.connection_manager.disconnect(node_id)
                logger.info(f"Node '{node_id}' disconnected gracefully: {payload.reason}")
        except Exception as e:
            logger.warning(f"Error parsing disconnect message: {e}")
        return None

    async def shutdown(self):
        tasks = list(getattr(self, "worker_tasks", {}).values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self.worker_tasks = {}
        self.latest_frames = {}
        self.frame_executor.shutdown(wait=True, cancel_futures=True)

    def handle_connection_loss(self, node_id: str) -> None:
        """Keep the authenticated session briefly so the same node can reconnect."""
        session = self.session_manager.get_session(node_id)
        if session:
            logger.info(
                "Socket lost for node '%s'; preserving session until heartbeat expiry.",
                node_id,
            )

    @staticmethod
    def _build_error(code: str, message: str, node_id: Optional[str] = None) -> dict:
        """Construct a strongly-typed ErrorMessage dict."""
        err = ErrorMessage(
            payload=ErrorPayload(
                node_id=node_id,
                error_code=code,
                message=message,
            )
        )
        return err.model_dump()


def _process_frame_worker(frame_b64: str, direction: str, capture_ts: float, upload_ts: float, rx_ts: float, frame_id: str = "NORTH-000000"):
    with _frame_worker_lock:
        return _process_frame_locked(frame_b64, direction, capture_ts, upload_ts, rx_ts, frame_id)


def _process_frame_locked(frame_b64: str, direction: str, capture_ts: float, upload_ts: float, rx_ts: float, frame_id: str):
    """
    Worker thread task executing CPU-bound base64/JPEG decoding, passing transport-agnostic np.ndarray
    frame into TrafficPipeline and ControlManager, and building immutable PipelineStateSnapshot.
    """
    import base64
    import cv2
    import numpy as np
    from core.application_context import ApplicationContext
    from ai.pipeline.traffic_pipeline import TrafficPipeline
    from ai.controller.control_manager import ControlManager

    if time.time() * 1000 - rx_ts > 2500:
        return None
    decode_start = time.time() * 1000.0
    if "," in frame_b64:
        frame_b64 = frame_b64.split(",")[1]
    frame_bytes = base64.b64decode(frame_b64, validate=True)
    nparr = np.frombuffer(frame_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    decode_ts = time.time() * 1000.0

    ctx = ApplicationContext.get_instance()

    if img is None:
        ctx.increment_stage_counter("decode_failed")
        return None

    ctx.increment_stage_counter("decoded")
    ctx.last_backend_decoded_frame_id = frame_id

    # Ensure TrafficPipeline and ControlManager are instantiated in ApplicationContext
    if ctx.pipeline is None:
        ctx.pipeline = TrafficPipeline(save_output=False, headless=True)
    if ctx.control_manager is None:
        ctx.control_manager = ControlManager(simulation_mode=True, headless=True)

    # 1. AI Perception, ByteTrack, Lane Assignment, Analytics & Signal Scheduler via TrafficPipeline
    yolo_start = int(time.time() * 1000)
    pipeline_result = ctx.pipeline.process_single_frame(img, lane_name=direction, timestamp=capture_ts / 1000)
    inference_time = int(time.time() * 1000)
    ctx.last_yolo_frame_id = frame_id
    ctx.last_tracked_frame_id = frame_id

    # 2. Control Layer execution via ControlManager (handles ESP32 hardware command & decision logging)
    ctx.control_manager.process_result(pipeline_result)
    scheduler_time = int(time.time() * 1000)

    # Extract annotated tile frame
    annotated_tile = pipeline_result.multi_annotated_frames.get(direction, img)
    ret, enc = cv2.imencode(".jpg", annotated_tile, [cv2.IMWRITE_JPEG_QUALITY, 80])
    annotated_bytes = enc.tobytes() if ret else frame_bytes

    # Build immutable PipelineStateSnapshot dict for main event loop atomic swap
    active_phase = (
        pipeline_result.intersection_state.green_lane
        if (pipeline_result.intersection_state and pipeline_result.intersection_state.green_lane)
        else direction.capitalize()
    )
    
    raw_detections_count = sum(len(dets) for dets in pipeline_result.multi_detections.values()) if pipeline_result.multi_detections else 0
    assigned_vehicles = (
        pipeline_result.intersection_state.total_vehicles
        if pipeline_result.intersection_state
        else 0
    )
    total_vehicles = assigned_vehicles
    rem_sec = pipeline_result.remaining_green_sec

    queue_len = 0.0
    pce_score = 0.0
    if pipeline_result.lane_stats:
        queue_len = round(sum(s.stopped_count for s in pipeline_result.lane_stats.values()), 1)
        pce_score = round(sum(s.pce_score for s in pipeline_result.lane_stats.values()), 1)

    # Display the same fairness-adjusted scores that selected the current phase.
    scores = getattr(pipeline_result.priority_result, "scores", []) or []
    priorities = {getattr(score.lane, "value", str(score.lane)).lower(): score.score for score in scores}
    lanes_payload = {}
    for d_name in ["north", "south", "east", "west"]:
        l_stat = pipeline_result.lane_stats.get(d_name) if pipeline_result.lane_stats else None
        if l_stat:
            v_cnt = int(getattr(l_stat, "live_count", 0))
            p_score = float(getattr(l_stat, "pce_score", 0.0))
            den = str(getattr(l_stat, "density", "LOW"))
            prio = round(priorities.get(d_name, 0.0), 2)
            raw_cnt = int(getattr(l_stat, "raw_count", v_cnt))
            sm_cnt = float(getattr(l_stat, "smoothed_count", float(v_cnt)))
            lanes_payload[d_name] = {
                "vehicles": v_cnt,
                "historicalCount": int(getattr(l_stat, "historical_count", 0)),
                "queue": int(getattr(l_stat, "stopped_count", 0)),
                "wait": round(float(getattr(l_stat, "max_queue_time_sec", 0)), 1),
                "pce": round(p_score, 1),
                "density": den,
                "priority": prio,
                "rawCount": raw_cnt,
                "smoothedCount": round(sm_cnt, 2),
            }
        else:
            lanes_payload[d_name] = {
                "vehicles": 0,
                "queue": 0.0,
                "wait": 0.0,
                "pce": 0.0,
                "density": "LOW",
                "priority": 0.0,
                "rawCount": 0,
                "smoothedCount": 0.0,
            }

    snapshot = {
        "protocol": "1.0",
        "type": "SystemStatusUpdated",
        "timestamp": time.time(),
        "payload": {
            "frameId": frame_id,
            "activePhase": active_phase,
            "signalState": pipeline_result.signal_state,
            "greenDuration": pipeline_result.signal_decision.green_duration_sec if pipeline_result.signal_decision else 0,
            "timeRemaining": rem_sec,
            "totalVehicles": total_vehicles,
            "detectedVehicles": raw_detections_count,
            "assignedVehicles": assigned_vehicles,
            "queueLength": queue_len,
            "pceScore": pce_score,
            "operatingMode": "AUTOMATIC",
            "frameProcessingErrors": getattr(ctx, "frame_processing_errors", 0),
            "latencyMetrics": getattr(pipeline_result, "latency_metrics", {}),
            "stabilityMetrics": getattr(pipeline_result, "stability_metrics", {}),
            "lanes": lanes_payload,
            "captureTimestamp": int(capture_ts),
            "uploadTimestamp": int(upload_ts),
            "backendReceiveTimestamp": int(rx_ts),
            "decodeTimestamp": int(decode_ts),
            "inferenceTimestamp": int(inference_time),
            "schedulerTimestamp": int(scheduler_time),
            "stageCounters": ctx.get_stage_counters(),
        },
    }

    telemetry = {
        "server_processing_ms": round(time.time() * 1000 - rx_ts, 2),
        "queue_wait_ms": round(decode_start - rx_ts, 2),
        "frame_id": frame_id,
        "vehicle_count": total_vehicles,
        "detected_count": raw_detections_count,
        "assigned_count": assigned_vehicles,
        "queue_length": queue_len,
        "pce_score": pce_score,
        "latency_metrics": getattr(pipeline_result, "latency_metrics", {}),
        "last_updated": time.time(),
    }

    return direction, annotated_bytes, snapshot, telemetry
