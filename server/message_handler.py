"""
MessageHandler parses incoming WebSocket JSON packets using Pydantic models,
delegates to SessionManager and ConnectionManager, and generates response payloads.
"""

import asyncio
import time
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

        # Validate protocol version — reject mismatched clients with a clear error
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

        payload_raw["node_id"] = node_id
        payload_raw["camera_direction"] = direction
        raw_json["payload"] = payload_raw

        try:
            msg = RegistrationMessage.model_validate(raw_json)
        except Exception as e:
            return self._build_error("INVALID_REGISTRATION_PAYLOAD", f"Schema validation error: {e}")

        payload = msg.payload
        session = self.session_manager.create_session(node_id, direction)
        await self.connection_manager.connect(node_id, websocket)

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
        logger.info(f"[PAIRING] REGISTER → ACK | node={node_id} | direction={direction} | token={session.session_token[:8]}...")

        # Schedule automatic START_STREAM signal to camera node so mobile app switches to STREAMING state
        async def _send_start_stream():
            await asyncio.sleep(0.1)
            start_msg = {
                "type": "START_STREAM",
                "message_type": "START_STREAM",
                "timestamp": time.time(),
                "payload": {
                    "target_fps": 30,
                    "resolution": "1280x720",
                    "quality": 80,
                },
            }
            await self.connection_manager.send_to_node(node_id, start_msg)
            logger.info(f"[PAIRING] Sent START_STREAM signal to camera node '{node_id}'")

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
        logger.debug(f"[PAIRING] HEARTBEAT → ACK | node={node_id}")
        return d

    async def _process_direction_loop(self, direction: str):
        """Worker task processing the latest queued frame for a specific lane direction."""
        logger.info(f"[LATENCY-CONTROL] Starting frame processing loop for lane '{direction}'")
        while True:
            if hasattr(self, "latest_frames") and self.latest_frames:
                logger.info(f"[LATENCY-CONTROL] worker loop for '{direction}' sees keys: {list(self.latest_frames.keys())}")
            raw_json = self.latest_frames.pop(direction, None) if hasattr(self, "latest_frames") else None
            if raw_json is None:
                await asyncio.sleep(0.01)  # 10ms poll interval
                continue

            try:
                payload_raw = raw_json.get("payload", {})
                frame_b64 = payload_raw.get("frame_data")
                if frame_b64:
                    from core.application_context import ApplicationContext
                    ctx = ApplicationContext.get_instance()
                    
                    # Read capture, upload, and receive times in milliseconds
                    cap_ts = payload_raw.get("capture_timestamp")
                    if cap_ts is None:
                        cap_ts = payload_raw.get("timestamp", time.time()) * 1000.0
                    upload_ts = payload_raw.get("upload_timestamp", cap_ts)
                    rx_ts = raw_json.get("backend_receive_timestamp", time.time() * 1000.0)

                    res = await asyncio.to_thread(_process_frame_worker, frame_b64, direction, cap_ts, upload_ts, rx_ts)
                    logger.info(f"[LATENCY-CONTROL] Background process worker finished. res is None: {res is None}")
                    if res:
                        dir_key, annotated_bytes, snapshot, telemetry = res
                        logger.info(f"[LATENCY-CONTROL] Updating snapshot in context. Snapshot type: {snapshot.get('type') if snapshot else None}")
                        await ctx.update_snapshot(snapshot)
                        ctx.frame_buffer[dir_key] = annotated_bytes
                        ctx.frame_buffer["active"] = annotated_bytes
                        ctx.live_telemetry[dir_key] = telemetry
                        ctx.increment_stage_counter("processed")
                    else:
                        ctx.frame_processing_errors += 1
            except Exception as e:
                logger.warning(f"Error in background frame processing loop for '{direction}': {e}", exc_info=True)

    async def _handle_video_frame(self, raw_json: dict) -> Optional[dict]:
        """Handle incoming VIDEO_FRAME payload by offloading to the corresponding direction queue."""
        payload_raw = raw_json.get("payload", {})
        if isinstance(payload_raw, dict):
            direction = (
                payload_raw.get("direction")
                or payload_raw.get("camera_direction")
                or payload_raw.get("assigned_direction")
                or "north"
            ).lower()

            # Lazy initialize worker states
            if not hasattr(self, "latest_frames"):
                self.latest_frames = {}
                self.dropped_frames_count = 0
                self.worker_tasks = {}

            # Log receive timestamp
            raw_json["backend_receive_timestamp"] = int(time.time() * 1000)

            from core.application_context import ApplicationContext
            ctx = ApplicationContext.get_instance()
            ctx.increment_stage_counter("received")

            # Latest Frame Wins Policy: check if there's already an unprocessed frame in the slot
            if direction in self.latest_frames:
                self.dropped_frames_count += 1
                ctx.increment_stage_counter("dropped")
                logger.info(f"[LATENCY-CONTROL] Dropping stale frame for '{direction}' (Total dropped: {self.dropped_frames_count})")

            self.latest_frames[direction] = raw_json

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

    def handle_connection_loss(self, node_id: str) -> None:
        """Handle unexpected WebSocket disconnect without explicit DISCONNECT packet."""
        self.session_manager.remove_session(node_id)

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


def _process_frame_worker(frame_b64: str, direction: str, capture_ts: float, upload_ts: float, rx_ts: float):
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

    decode_start = time.time() * 1000.0
    if "," in frame_b64:
        frame_b64 = frame_b64.split(",")[1]
    frame_bytes = base64.b64decode(frame_b64)
    nparr = np.frombuffer(frame_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    decode_ts = time.time() * 1000.0

    ctx = ApplicationContext.get_instance()
    ctx.increment_stage_counter("decoded")

    if img is None:
        ctx.increment_stage_counter("decode_failed")
        return None

    # Ensure TrafficPipeline and ControlManager are instantiated in ApplicationContext
    if ctx.pipeline is None:
        ctx.pipeline = TrafficPipeline(save_output=False)
    if ctx.control_manager is None:
        ctx.control_manager = ControlManager(simulation_mode=True)

    # 1. AI Perception, ByteTrack, Lane Assignment, Analytics & Signal Scheduler via TrafficPipeline
    yolo_start = int(time.time() * 1000)
    pipeline_result = ctx.pipeline.process_single_frame(img, lane_name=direction)
    inference_time = int(time.time() * 1000)

    # 2. Control Layer execution via ControlManager (handles ESP32 hardware command & decision logging)
    ctx.control_manager.process_result(pipeline_result)
    scheduler_time = int(time.time() * 1000)

    # Extract annotated tile frame
    annotated_tile = pipeline_result.multi_annotated_frames.get(direction, img)
    ret, enc = cv2.imencode(".jpg", annotated_tile)
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
    total_vehicles = max(raw_detections_count, assigned_vehicles)
    rem_sec = pipeline_result.remaining_green_sec

    queue_len = 0.0
    pce_score = 0.0
    if pipeline_result.lane_stats:
        queue_len = round(sum(s.total_queue_time_sec for s in pipeline_result.lane_stats.values()), 1)
        pce_score = round(sum(s.pce_score for s in pipeline_result.lane_stats.values()), 1)

    lanes_payload = {}
    for d_name in ["north", "south", "east", "west"]:
        l_stat = pipeline_result.lane_stats.get(d_name) if pipeline_result.lane_stats else None
        if l_stat:
            v_cnt = int(getattr(l_stat, "live_count", 0))
            q_val = float(getattr(l_stat, "total_queue_time_sec", 0.0))
            p_score = float(getattr(l_stat, "pce_score", 0.0))
            den = str(getattr(l_stat, "density", "LOW"))
            prio = round(v_cnt * 0.5 + p_score * 0.5, 2)
            # Phase 3.5: Include stabilization telemetry per lane
            raw_cnt = int(getattr(l_stat, "raw_count", v_cnt))
            sm_cnt = float(getattr(l_stat, "smoothed_count", float(v_cnt)))
            lanes_payload[d_name] = {
                "vehicles": v_cnt,
                "queue": round(q_val, 1),
                "wait": round(q_val, 1),
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
            "activePhase": active_phase,
            "greenDuration": 25,
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
        "vehicle_count": total_vehicles,
        "detected_count": raw_detections_count,
        "assigned_count": assigned_vehicles,
        "queue_length": queue_len,
        "pce_score": pce_score,
        "latency_metrics": getattr(pipeline_result, "latency_metrics", {}),
        "last_updated": time.time(),
    }

    return direction, annotated_bytes, snapshot, telemetry
