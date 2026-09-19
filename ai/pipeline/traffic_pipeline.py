"""
TrafficPipeline orchestrates full multi-camera execution flow across Perception,
Traffic Analytics, and Adaptive Signal Decision Engine layers using structured dataclass pipelines.
"""

from pathlib import Path
from typing import Optional, Union, Dict, Any, List
import time
import math
import cv2
import numpy as np

from config.paths import get_timestamped_output_path
from ai.camera import CameraManager
from ai.models.model_manager import ModelManager
from ai.detection.detector import VehicleDetector
from ai.tracking.byte_tracker import ByteTracker
from ai.lane.lane_manager import LaneManager
from ai.state.vehicle_state_manager import VehicleStateManager
from ai.state.count_stabilizer import CountStabilizer
from ai.analytics.analytics_exporter import AnalyticsExporter, LaneStatistics
from ai.signal import (
    PriorityCalculator,
    EmergencyOverride,
    SignalScheduler,
    SignalController,
    PriorityResult,
    SignalDecision,
    HardwareCommand,
)
from ai.visualization.visualizer import Visualizer
from dashboard.multi_camera_dashboard import MultiCameraDashboard
from ai.utils.statistics import StatisticsTracker
from ai.pipeline.pipeline_health import PipelineHealth
from ai.pipeline.intersection_state import LaneProcessingResult, IntersectionState
from ai.pipeline.pipeline_result import PipelineResult
from ai.utils.logger import get_logger
from config.signal import EMPTY_LANE_RELEASE_SEC, ALL_RED_SEC
from config.model import DETECTOR_FPS

import threading

logger = get_logger("TrafficPipeline")


def detector_is_due(last_detection_ts: Optional[float], frame_ts: float, detector_fps: float) -> bool:
    """Time-based cadence gate, independent of input frame rate."""
    return (last_detection_ts is None or frame_ts < last_detection_ts
            or frame_ts - last_detection_ts >= 1.0 / detector_fps)


class TrafficPipeline:
    """
    Production multi-camera execution pipeline connecting 4-Camera Ingestion,
    Perception (single configured YOLO+ByteTrack forward pass per frame), Traffic Analytics
    (Lane, Vehicle State, PCE, Queue), and Adaptive Signal Decision Engine.

    One shared detector performs one inference per frame. Independent ByteTrack
    instances associate detections within each camera without invoking the model.
    """

    def __init__(
        self,
        camera_manager: Optional[CameraManager] = None,
        video_source: Optional[Union[str, Path, int]] = None,
        save_output: bool = True,
        output_path: Optional[Path] = None,
        headless: bool = False,
    ):
        logger.info("Initializing Smart Traffic Management System Pipeline...")

        # Thread Safety Re-entrant Lock & Per-Lane Locks
        self._lock = threading.RLock()
        self.headless = headless
        self._lane_locks: Dict[str, threading.Lock] = {
            "north": threading.Lock(),
            "south": threading.Lock(),
            "east": threading.Lock(),
            "west": threading.Lock(),
        }

        # 1. Ingestion Layer (CameraManager)
        if camera_manager is not None:
            self.camera_manager = camera_manager
        elif video_source is not None:
            self.camera_manager = CameraManager(config=video_source)
        else:
            self.camera_manager = CameraManager(config={})

        # 2. Perception & Analytics Layer (Shared Vision Model, Per-Lane Trackers & State Managers)
        self.model_manager = ModelManager()
        self.detector = VehicleDetector(model_manager=self.model_manager)

        self.trackers: Dict[str, ByteTracker] = {}
        self.lane_managers: Dict[str, LaneManager] = {}
        self.state_managers: Dict[str, VehicleStateManager] = {}
        self.analytics_exporters: Dict[str, AnalyticsExporter] = {}
        self._last_detection_ts: Dict[str, float] = {}
        self._last_detection_frame: Dict[str, int] = {}
        self._last_tracked_frame: Dict[str, int] = {}
        self._last_prediction_frame: Dict[str, int] = {}
        self._detector_runs: Dict[str, int] = {}
        self._tracker_runs: Dict[str, int] = {}
        self._temporal_started_at: Dict[str, float] = {}
        self._last_authoritative_stats: Dict[str, LaneStatistics] = {}

        # Initialize per-lane perception & analytics components
        for lane_name, stream in self.camera_manager.streams.items():
            self._init_lane_components(lane_name, stream.resolution)

        # 3. Adaptive Signal Decision Layer
        self.priority_calculator = PriorityCalculator()
        self.emergency_override = EmergencyOverride()
        self.signal_scheduler = SignalScheduler()
        self.signal_controller = SignalController()

        # 4. Signal Phase Timer State Machine & Monotonic Phase Counter
        self.phase_counter: int = 0
        self.active_decision: Optional[SignalDecision] = None
        self.active_hardware_cmd: Optional[HardwareCommand] = None
        self.last_priority_result: Optional[PriorityResult] = None
        self.phase_start_time: float = 0.0
        self._active_empty_since: Optional[float] = None

        # 5. Output Video Recording Path
        if save_output and output_path is None:
            output_path = get_timestamped_output_path(prefix="multi_camera_system")

        # 5.5 Phase 3.5 — Vehicle Count Stabilizer (EMA smoothing before scheduler)
        self.count_stabilizer = CountStabilizer()

        # 6. Visualizer Engine & Dashboard UI
        self.visualizer = Visualizer(save_video=save_output, output_path=output_path)
        self.dashboard = MultiCameraDashboard(tile_width=640, tile_height=360)

        # 7. Performance Statistics Monitor
        self.stats = StatisticsTracker()

        logger.info("Multi-Camera Traffic Management Pipeline fully initialized and ready!")

    def _init_lane_components(self, lane_name: str, resolution: tuple) -> None:
        """Initialize perception and state tracking modules for a specific camera direction."""
        res_w, res_h = resolution
        w = res_w if res_w > 0 else 1280
        h = res_h if res_h > 0 else 720

        self.trackers[lane_name] = ByteTracker(model_manager=self.model_manager)
        self.lane_managers[lane_name] = LaneManager(frame_width=w, frame_height=h)
        self.state_managers[lane_name] = VehicleStateManager()
        self.analytics_exporters[lane_name] = AnalyticsExporter()

    def process_single_frame(
        self, frame: np.ndarray, lane_name: str = "north", timestamp: Optional[float] = None,
        precomputed_detection=None,
    ) -> PipelineResult:
        """
        Transport-agnostic frame processor accepting a decoded numpy image frame.
        Ignorant of WebSocket, RTSP, or USB network protocols.
        """
        ts = timestamp or time.time()
        frames_data = {
            lane_name.lower(): {
                "frame": frame,
                "connected": True,
                "frame_number": getattr(self, "_frame_count", 0) + 1,
                "timestamp": ts,
                "fps": None,
                "resolution": (frame.shape[1], frame.shape[0]) if frame is not None else (1280, 720),
            }
        }
        self._frame_count = getattr(self, "_frame_count", 0) + 1
        if precomputed_detection is not None:
            frames_data[lane_name.lower()]["precomputed_detection"] = precomputed_detection
        return self.process_step(frames_data=frames_data)

    def process_step(
        self, frames_data: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> PipelineResult:
        """
        Execute one multi-camera pipeline step with thread-safe lock acquisition.
        Per-lane processing locks ensure independent camera streams execute perception
        and analytics concurrently without global worker serialization.
        """
        # Perception and scheduler share mutable state. YOLO already serializes inference.
        with self._lock:
            return self._process_step_unlocked(frames_data=frames_data)

    def _process_step_unlocked(
        self, frames_data: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> PipelineResult:
        t_start = time.perf_counter()
        if frames_data is None:
            frames_data = self.camera_manager.read_all()

        if not frames_data and not self.active_decision:
            return PipelineResult(has_frame=False)

        lane_results: Dict[str, LaneProcessingResult] = {}
        lane_stats_map: Dict[str, LaneStatistics] = {}
        observed_stats_map: Dict[str, LaneStatistics] = {}
        multi_detections: Dict[str, List[Any]] = {}
        multi_annotated_frames: Dict[str, np.ndarray] = {}
        max_inference_ms = 0.0
        max_tracking_ms = 0.0
        analytics_ms = 0.0

        # Step 1-5: Process each camera feed independently
        for lane_name, payload in frames_data.items():
            frame = payload.get("frame")
            connected = payload.get("connected", False)
            frame_num = payload.get("frame_number", 0)
            timestamp = payload.get("timestamp", time.time())
            fps = payload.get("fps")

            if not connected or frame is None:
                # Provide fallback zero statistics for disconnected camera feed
                fallback_stat = LaneStatistics(
                    lane_name=lane_name,
                    live_count=0,
                    total_queue_time_sec=0.0,
                    pce_score=0.0,
                    density="LOW",
                )
                lane_stats_map[lane_name] = fallback_stat
                lane_results[lane_name] = LaneProcessingResult(
                    lane_name=lane_name,
                    raw_frame=None,
                    annotated_frame=None,
                    detections=[],
                    statistics=fallback_stat,
                    connected=False,
                    fps=0.0,
                    timestamp=timestamp,
                )
                continue

            # Ensure lane perception components exist
            if lane_name not in self.trackers:
                resolution = payload.get("resolution", (1280, 720))
                self._init_lane_components(lane_name, resolution)

            # YOLO runs at a configurable cadence. ByteTrack projects active
            # identities on intermediate fresh frames without fake detections.
            last_detection_ts = self._last_detection_ts.get(lane_name)
            detector_due = detector_is_due(last_detection_ts, timestamp, DETECTOR_FPS)
            if detector_due:
                if "precomputed_detection" in payload:
                    detections, inference_ms = payload["precomputed_detection"]
                else:
                    detections, inference_ms = self.detector.detect(
                        frame, frame_number=frame_num, timestamp=timestamp
                    )
                tracking_start = time.perf_counter()
                tracked_detections = self.trackers[lane_name].update(
                    detections, frame=frame, frame_number=frame_num, timestamp=timestamp
                )
                self._last_detection_ts[lane_name] = timestamp
                self._last_detection_frame[lane_name] = frame_num
                self._detector_runs[lane_name] = self._detector_runs.get(lane_name, 0) + 1
                max_inference_ms = max(max_inference_ms, inference_ms)
            else:
                tracking_start = time.perf_counter()
                tracked_detections = self.trackers[lane_name].predict(
                    frame_number=frame_num, timestamp=timestamp
                )
                self._last_prediction_frame[lane_name] = frame_num
            max_tracking_ms = max(max_tracking_ms, (time.perf_counter() - tracking_start) * 1000.0)
            self._last_tracked_frame[lane_name] = frame_num
            self._tracker_runs[lane_name] = self._tracker_runs.get(lane_name, 0) + 1
            self._temporal_started_at.setdefault(lane_name, time.monotonic())

            # Step 3: Bind observations to the registered approach.
            w_f, h_f = frame.shape[1], frame.shape[0]
            # Each camera watches a single approach, not a bird's-eye intersection.
            from dataclasses import replace
            lane_detections = [replace(d, lane=lane_name.capitalize()) for d in tracked_detections]

            # Step 4-5: only detector observations mutate vehicle state or
            # authoritative analytics. Predictions remain display-only.
            if detector_due:
                analytics_start = time.perf_counter()
                enriched_detections = self.state_managers[lane_name].update(
                    lane_detections, frame_number=frame_num, timestamp=timestamp
                )
                stats_map = self.analytics_exporters[lane_name].generate_stats(
                    self.state_managers[lane_name]
                )
                lane_stat = stats_map.get(lane_name) or stats_map.get(lane_name.capitalize())
                if lane_stat is None and stats_map:
                    first_stat = next(iter(stats_map.values()))
                    total_vehicles = sum(s.live_count for s in stats_map.values())
                    total_queue = sum(s.total_queue_time_sec for s in stats_map.values())
                    total_pce = sum(s.pce_score for s in stats_map.values())
                    has_emergency = any(s.has_priority_vehicle for s in stats_map.values())
                    lane_stat = LaneStatistics(
                        lane_name=lane_name,
                        live_count=total_vehicles,
                        total_queue_time_sec=total_queue,
                        pce_score=total_pce,
                        density=first_stat.density,
                        has_priority_vehicle=has_emergency,
                    )
                elif lane_stat is None:
                    lane_stat = LaneStatistics(lane_name=lane_name, live_count=len(enriched_detections))
                observed_stats_map[lane_name] = lane_stat
                analytics_ms += (time.perf_counter() - analytics_start) * 1000.0
            else:
                enriched_detections = lane_detections
                lane_stat = self._last_authoritative_stats.get(
                    lane_name, LaneStatistics(lane_name=lane_name)
                )
                stats_map = {lane_name.capitalize(): lane_stat}

            lane_stats_map[lane_name] = lane_stat
            multi_detections[lane_name] = enriched_detections

            # Render individual tile frame annotation with visualizer
            annotated_tile = self.visualizer.draw(
                frame=frame,
                detections=enriched_detections,
                lane_manager=None,  # One camera covers one approach; no arbitrary quadrant ROIs.
                lane_stats=stats_map,
                source_fps=fps,
            )
            multi_annotated_frames[lane_name] = annotated_tile
            payload["frame"] = annotated_tile

            # Build LaneProcessingResult dataclass
            lane_results[lane_name] = LaneProcessingResult(
                lane_name=lane_name,
                raw_frame=frame,
                annotated_frame=annotated_tile,
                detections=enriched_detections,
                statistics=lane_stat,
                connected=True,
                fps=fps,
                timestamp=timestamp,
            )

        # Build unified IntersectionState dataclass with multi-lane state persistence & 15s decay policy
        from core.application_context import ApplicationContext
        ctx = ApplicationContext.get_instance()
        now_mono = time.monotonic()

        if observed_stats_map:
            analytics_start = time.perf_counter()
            stabilized = self.count_stabilizer.stabilize(
                observed_stats_map, timestamp=time.time()
            )
            self._last_authoritative_stats.update(stabilized)
            lane_stats_map.update(stabilized)
            analytics_ms += (time.perf_counter() - analytics_start) * 1000.0

        # Update persistent history with fresh lane stats
        for l_name, l_stat in lane_stats_map.items():
            ctx.lane_stats_history[l_name] = l_stat
            ctx.lane_last_seen[l_name] = now_mono

        # Merge historical lane stats for non-active lanes, applying 15s stale decay policy
        all_intersection_lanes: Dict[str, LaneStatistics] = {}
        all_known_lanes = set(list(lane_stats_map.keys()) + list(ctx.lane_stats_history.keys()) + ["north", "east", "south", "west"])

        for l_name in all_known_lanes:
            if l_name in lane_stats_map:
                all_intersection_lanes[l_name] = lane_stats_map[l_name]
            elif l_name in ctx.lane_stats_history:
                hist_stat = ctx.lane_stats_history[l_name]
                last_seen = ctx.lane_last_seen.get(l_name, 0.0)
                if now_mono - last_seen > 3.0:
                    # 15s Stale Decay: clear vehicle queue metrics for offline camera feed
                    decayed_stat = LaneStatistics(
                        lane_name=hist_stat.lane_name,
                        live_count=0,
                        total_queue_time_sec=0.0,
                        pce_score=0.0,
                        density="LOW",
                        has_priority_vehicle=False,
                    )
                    ctx.lane_stats_history[l_name] = decayed_stat
                    all_intersection_lanes[l_name] = decayed_stat
                else:
                    all_intersection_lanes[l_name] = hist_stat
            else:
                all_intersection_lanes[l_name] = LaneStatistics(lane_name=l_name, live_count=0)

        lane_stats_map = all_intersection_lanes

        # Queue values remain vehicle counts unless an approach-specific
        # ground-plane calibration explicitly supplies metric evidence.
        for lane_stat in lane_stats_map.values():
            lane_stat.queue_value = float(lane_stat.stopped_count)
            lane_stat.queue_unit = "vehicles"
            lane_stat.queue_calibrated = False
            lane_stat.queue_calibration_id = None

        # ── Phase 3.5: Vehicle Count Stabilization ───────────────────────────
        # Apply EMA smoothing to lane counts before scheduler evaluation.
        # This prevents scheduler flicker from one-frame detection noise,
        # temporary occlusions, or track ID switches.

        total_intersection_vehicles = sum(s.live_count for s in lane_stats_map.values())
        intersection_state = IntersectionState(
            lanes=lane_stats_map,
            timestamp=time.time(),
            total_vehicles=total_intersection_vehicles,
            active_phase_id=self.phase_counter,
            green_lane=self.active_decision.green_lane.value if self.active_decision else None,
        )

        # Step 6: Signal Decision Engine Execution
        scheduler_start = time.perf_counter()
        has_emergency = any(s.has_priority_vehicle for s in lane_stats_map.values())

        current_mono_time = time.monotonic()
        elapsed_sec = current_mono_time - self.phase_start_time if self.phase_start_time > 0 else 999.0

        # When the currently green approach becomes empty, end green after a
        # short confirmation window. Yellow and all-red clearance still run;
        # the next occupied approach is then selected by the cycle cursor.
        if self.active_decision:
            active_key = getattr(self.active_decision.green_lane, "value", str(self.active_decision.green_lane)).lower()
            active_stats = lane_stats_map.get(active_key)
            has_fresh_active_observation = active_key in frames_data
            active_is_empty = bool(
                has_fresh_active_observation
                and active_stats is not None
                and active_stats.raw_count == 0
            )
            if active_is_empty:
                if self._active_empty_since is None:
                    self._active_empty_since = current_mono_time
                elif (
                    current_mono_time - self._active_empty_since >= EMPTY_LANE_RELEASE_SEC
                    and elapsed_sec < self.active_decision.green_duration_sec
                ):
                    self.active_decision.green_duration_sec = max(1, int(math.floor(elapsed_sec)))
                    logger.info("[SCHEDULER EVENT] ending empty lane '%s' green early", active_key)
            elif has_fresh_active_observation:
                self._active_empty_since = None

        is_phase_expired = (
            self.active_decision is None
            or elapsed_sec >= (
                self.active_decision.green_duration_sec
                + self.active_decision.yellow_duration_sec
                + ALL_RED_SEC
            )
        )

        is_phase_change = False

        if is_phase_expired or (has_emergency and self.active_decision and self.active_decision.reason.value != "EMERGENCY"):
            old_phase = self.active_decision.green_lane if self.active_decision else "None"
            is_phase_change = True
            self.phase_counter += 1

            # Priority Calculation across all 4 approach lanes
            base_priority_result = self.priority_calculator.calculate(lane_stats_map)

            # Emergency Vehicle Override
            final_priority_result = self.emergency_override.check_and_override(
                base_priority_result, lane_stats_map
            )

            fresh_lanes = {name for name in lane_stats_map if now_mono - ctx.lane_last_seen.get(name, 0) < 3}
            final_priority_result, _ = self.signal_scheduler.select_eligible(
                final_priority_result, lane_stats_map, fresh_lanes)
            if final_priority_result is None:
                self.active_decision = None
                self.active_hardware_cmd = None
                return PipelineResult(has_frame=bool(frames_data), lane_stats=lane_stats_map,
                    intersection_state=intersection_state, signal_state="ALL_RED",
                    multi_detections=multi_detections,
                    multi_annotated_frames=multi_annotated_frames,
                    latency_metrics={"yolo_ms": round(max_inference_ms, 2),
                        "tracking_ms": round(max_tracking_ms, 2),
                        "analytics_ms": round(analytics_ms, 2),
                        "scheduler_ms": round((time.perf_counter() - scheduler_start) * 1000.0, 2),
                        "detector_ran": max_inference_ms > 0,
                        "total_ms": round((time.perf_counter() - t_start) * 1000, 2)})
            self.active_decision = self.signal_scheduler.schedule(final_priority_result, phase_id=self.phase_counter)
            from ai.signal.signal_types import DecisionReason
            selected_key = getattr(
                self.active_decision.green_lane, "value", str(self.active_decision.green_lane)
            ).lower()
            if lane_stats_map[selected_key].has_priority_vehicle:
                self.active_decision.reason = DecisionReason.EMERGENCY
                self.active_decision.reason_details = "Fresh emergency vehicle detection pre-empted the normal cycle"
            self.last_priority_result = final_priority_result
            self.phase_start_time = current_mono_time
            self._active_empty_since = None

            # Phase 3.5: Track scheduler decision stability
            green_lane_str = (
                self.active_decision.green_lane.value
                if hasattr(self.active_decision.green_lane, 'value')
                else str(self.active_decision.green_lane)
            )
            self.count_stabilizer.update_decision_stability(green_lane_str, timestamp=time.time())

            # Hardware Command Generation for ESP32
            self.active_hardware_cmd = self.signal_controller.generate_command(self.active_decision)
            logger.info(
                f"[SCHEDULER EVENT] scheduler_phase_changed | old_phase='{old_phase}' -> new_phase='{self.active_decision.green_lane}' "
                f"| duration={self.active_decision.green_duration_sec}s | phase_id={self.phase_counter}"
            )

        # Calculate remaining green phase seconds using monotonic clock deltas
        remaining_green_sec = 0
        if self.active_decision:
            green_duration = self.active_decision.green_duration_sec
            remaining_green_sec = max(0, int(math.ceil(green_duration - (current_mono_time - self.phase_start_time))))

        intersection_state.active_phase_id = self.phase_counter
        intersection_state.green_lane = self.active_decision.green_lane.value if self.active_decision else None
        intersection_state.remaining_green_sec = remaining_green_sec
        scheduler_ms = (time.perf_counter() - scheduler_start) * 1000.0

        # Pipeline Health Diagnostics
        primary_lane = next(iter(multi_detections.keys())) if multi_detections else "north"
        health = PipelineHealth.evaluate(
            raw_detections=multi_detections.get(primary_lane, []),
            tracked_detections=multi_detections.get(primary_lane, []),
            lane_stats=lane_stats_map,
            priority_result=self.last_priority_result,
            decision=self.active_decision,
            hardware_cmd=self.active_hardware_cmd,
            phase_id=self.phase_counter,
            remaining_time_sec=remaining_green_sec,
        )

        if frames_data:
            self.stats.record_frame(max_inference_ms)

        # Render MultiCameraDashboard composite canvas
        composite_dashboard = None if self.headless else self.dashboard.render(
            stream_data=frames_data,
            intersection_state=lane_stats_map,
            signal_decision=self.active_decision,
            remaining_green_sec=remaining_green_sec,
        )

        primary_dets = multi_detections.get(primary_lane, [])

        t_total_ms = (time.perf_counter() - t_start) * 1000.0
        frame_id = getattr(self, "_frame_count", 1)
        latency_metrics = {
            "frame_id": frame_id,
            "timestamp": round(time.time(), 3),
            "yolo_ms": round(max_inference_ms, 2),
            "tracking_ms": round(max_tracking_ms, 2),
            "analytics_ms": round(analytics_ms, 2),
            "scheduler_ms": round(scheduler_ms, 2),
            "total_ms": round(t_total_ms, 2),
            "detector_fps_target": DETECTOR_FPS,
            "detector_ran": max_inference_ms > 0,
            "last_detection_frame": self._last_detection_frame.get(primary_lane),
            "last_prediction_frame": self._last_prediction_frame.get(primary_lane),
            "last_tracked_frame": self._last_tracked_frame.get(primary_lane),
            "detector_fps": round(self._detector_runs.get(primary_lane, 0) / max(0.001, time.monotonic() - self._temporal_started_at.get(primary_lane, time.monotonic())), 2),
            "tracker_fps": round(self._tracker_runs.get(primary_lane, 0) / max(0.001, time.monotonic() - self._temporal_started_at.get(primary_lane, time.monotonic())), 2),
        }
        logger.debug(
            f"[LATENCY TRACE] Frame #{frame_id} | Total Step: {t_total_ms:.1f}ms | Max YOLO: {max_inference_ms:.1f}ms | "
            f"Active Phase: '{intersection_state.green_lane}' ({remaining_green_sec}s left)"
        )

        return PipelineResult(
            has_frame=True,
            annotated_frame=composite_dashboard,
            lane_results=lane_results,
            intersection_state=intersection_state,
            detections=primary_dets,
            lane_stats=lane_stats_map,
            multi_detections=multi_detections,
            multi_annotated_frames=multi_annotated_frames,
            priority_result=self.last_priority_result,
            signal_decision=self.active_decision,
            hardware_command=self.active_hardware_cmd,
            health=health,
            remaining_green_sec=remaining_green_sec,
            signal_state=("GREEN" if current_mono_time - self.phase_start_time < self.active_decision.green_duration_sec
                else "YELLOW" if current_mono_time - self.phase_start_time < self.active_decision.green_duration_sec + self.active_decision.yellow_duration_sec
                else "ALL_RED") if self.active_decision else "ALL_RED",
            is_phase_change=is_phase_change,
            latency_metrics=latency_metrics,
            stability_metrics=self.count_stabilizer.metrics.to_dict(),
        )

    def release(self) -> None:
        """Release pipeline and camera manager resources."""
        logger.info("Shutting down Multi-Camera Traffic Pipeline...")
        if self.camera_manager:
            self.camera_manager.stop_all()
        self.visualizer.release()

        # Phase 3.5: Flush scheduler input report on shutdown
        self.count_stabilizer.flush_report()

        summary = self.stats.get_summary()
        logger.info(
            f"Pipeline Session Summary: Processed {summary['total_frames']} frames in "
            f"{summary['elapsed_seconds']}s (Avg FPS: {summary['average_fps']}, "
            f"Avg Latency: {summary['avg_inference_ms']}ms)"
        )
