"""
TrafficPipeline orchestrates full execution flow across Perception, Traffic Analytics, and Signal Decision layers.
Includes a phase timer state machine so signal decisions recompute only on phase expiration or emergency override.
"""

from pathlib import Path
from typing import Optional, Union, Dict, Any
import time
import cv2
import numpy as np

from config.paths import DEFAULT_VIDEO_PATH, get_timestamped_output_path
from ai.camera.camera_manager import CameraManager
from ai.models.model_manager import ModelManager
from ai.detection.detector import VehicleDetector
from ai.tracking.byte_tracker import ByteTracker
from ai.lane.lane_manager import LaneManager
from ai.state.vehicle_state_manager import VehicleStateManager
from ai.analytics.analytics_exporter import AnalyticsExporter
from ai.signal import (
    PriorityCalculator,
    FairnessManager,
    EmergencyOverride,
    SignalScheduler,
    SignalController,
    PriorityResult,
    SignalDecision,
    HardwareCommand,
)
from ai.visualization.visualizer import Visualizer
from ai.utils.statistics import StatisticsTracker
from ai.pipeline.pipeline_result import PipelineResult
from ai.utils.logger import get_logger

logger = get_logger("TrafficPipeline")


class TrafficPipeline:
    """
    Production execution pipeline connecting Perception (Camera, YOLO, ByteTrack),
    Traffic Analytics (Lane, State, Occupancy, Congestion), and Adaptive Signal Decision Engine
    (PriorityCalculator, FairnessManager, EmergencyOverride, SignalScheduler, SignalController).
    """

    def __init__(
        self,
        video_source: Union[str, Path, int] = DEFAULT_VIDEO_PATH,
        save_output: bool = True,
        output_path: Optional[Path] = None,
    ):
        logger.info("Initializing Smart Traffic Management System Pipeline...")

        # 1. Perception Layer (Camera Ingestion, Vision Model, Tracker)
        self.camera_manager = CameraManager(source=video_source)
        res_w, res_h = self.camera_manager.resolution

        self.model_manager = ModelManager()
        self.detector = VehicleDetector(model_manager=self.model_manager)
        self.tracker = ByteTracker(model_manager=self.model_manager)

        # 2. Traffic Analytics Layer (Lane ROIs, Vehicle State, Analytics Exporter)
        self.lane_manager = LaneManager(
            frame_width=res_w if res_w > 0 else 1280,
            frame_height=res_h if res_h > 0 else 720,
        )
        self.state_manager = VehicleStateManager()
        self.analytics_exporter = AnalyticsExporter()

        # 3. Adaptive Signal Decision Layer
        self.priority_calculator = PriorityCalculator()
        self.fairness_manager = FairnessManager()
        self.emergency_override = EmergencyOverride()
        self.signal_scheduler = SignalScheduler()
        self.signal_controller = SignalController()

        # 4. Signal Phase Timer State Machine
        self.active_decision: Optional[SignalDecision] = None
        self.active_hardware_cmd: Optional[HardwareCommand] = None
        self.last_priority_result: Optional[PriorityResult] = None
        self.phase_start_time: float = 0.0

        # 5. Output Video Recording Path
        if save_output and output_path is None:
            output_path = get_timestamped_output_path(prefix="traffic_system")

        # 6. Visualizer Renderer
        self.visualizer = Visualizer(save_video=save_output, output_path=output_path)

        # 7. Performance Statistics Monitor
        self.stats = StatisticsTracker()

        logger.info("Smart Traffic Management System Pipeline fully initialized and ready!")

    def process_step(self) -> PipelineResult:
        """
        Execute one step of the pipeline for a single frame.
        Perception & Analytics run every frame at 30 FPS.
        Signal Decision Engine executes ONLY when the current phase timer expires or emergency vehicle arrives.
        
        Returns:
            PipelineResult: Strongly-typed container holding all step outputs.
        """
        success, frame, frame_num, timestamp = self.camera_manager.get_frame()
        if not success or frame is None:
            return PipelineResult(has_frame=False)

        # Step 1: Perception (YOLO Detection - Runs every frame)
        raw_detections, inference_ms = self.detector.detect(
            frame, frame_number=frame_num, timestamp=timestamp
        )

        # Step 2: Perception (ByteTrack Vehicle Tracking - Runs every frame)
        tracked_detections = self.tracker.update(
            raw_detections, frame=frame, frame_number=frame_num, timestamp=timestamp
        )

        # Step 3: Analytics (Geometric Lane Assignment - Runs every frame)
        lane_detections = self.lane_manager.assign_lanes(tracked_detections)

        # Step 4: Analytics (Vehicle State & Motion Tracking - Runs every frame)
        enriched_detections = self.state_manager.update(
            lane_detections, frame_number=frame_num, timestamp=timestamp
        )

        # Step 5: Analytics (LaneStatistics Generation - Runs every frame)
        lane_stats = self.analytics_exporter.generate_stats(self.state_manager)

        # Perception-to-Analytics Data Binding Sanity Check
        total_live_vehicles = sum(s.live_count for s in lane_stats.values())
        if len(enriched_detections) > 0 and total_live_vehicles == 0:
            logger.warning(
                f"⚠️ [Data Binding Warning] {len(enriched_detections)} detections exist "
                f"but 0 mapped to active lane statistics!"
            )

        # Check for Emergency Vehicle Priority Trigger
        has_emergency = any(s.has_priority_vehicle for s in lane_stats.values())

        # Calculate Phase Timer Countdown
        current_time = time.time()
        elapsed_sec = current_time - self.phase_start_time if self.phase_start_time > 0 else 999.0
        
        is_phase_expired = (
            self.active_decision is None
            or elapsed_sec >= (self.active_decision.green_duration_sec + self.active_decision.yellow_duration_sec)
        )

        is_phase_change = False

        # Execute Decision Engine ONLY when current phase expires OR emergency vehicle arrives
        if is_phase_expired or has_emergency:
            is_phase_change = True
            
            # Step 6: Priority Calculator
            base_priority_result = self.priority_calculator.calculate(lane_stats)

            # Step 7: Starvation Fairness Manager
            fairness_priority_result = self.fairness_manager.apply_fairness(base_priority_result)

            # Step 8: Emergency Vehicle Override
            final_priority_result = self.emergency_override.check_and_override(
                fairness_priority_result, lane_stats
            )

            # Step 9: Signal Scheduler (Choose Winner & Duration)
            self.active_decision = self.signal_scheduler.schedule(final_priority_result)
            self.last_priority_result = final_priority_result
            self.phase_start_time = current_time

            # Update FairnessManager served state
            self.fairness_manager.update_served(self.active_decision.green_lane)

            # Step 10: Hardware Command Generation for ESP32
            self.active_hardware_cmd = self.signal_controller.generate_command(self.active_decision)

        # Calculate remaining green phase duration
        remaining_green_sec = 0
        if self.active_decision:
            green_duration = self.active_decision.green_duration_sec
            remaining_green_sec = max(0, int(round(green_duration - (current_time - self.phase_start_time))))

        # Step 11: Performance Monitoring
        self.stats.record_frame(inference_ms)

        # Step 12: Render Frame Annotations, Debug Badges, ROIs, and Analytics/Decision HUD Panel
        annotated_frame = self.visualizer.draw(
            frame=frame,
            detections=enriched_detections,
            lane_manager=self.lane_manager,
            lane_stats=lane_stats,
            decision=self.active_decision,
            remaining_green_sec=remaining_green_sec,
            stats=self.stats,
            source_fps=self.camera_manager.fps,
        )

        return PipelineResult(
            has_frame=True,
            annotated_frame=annotated_frame,
            detections=enriched_detections,
            lane_stats=lane_stats,
            priority_result=self.last_priority_result,
            signal_decision=self.active_decision,
            hardware_command=self.active_hardware_cmd,
            remaining_green_sec=remaining_green_sec,
            is_phase_change=is_phase_change,
        )

    def release(self) -> None:
        """Release pipeline resources."""
        logger.info("Shutting down Traffic Pipeline...")
        self.camera_manager.release()
        self.visualizer.release()

        summary = self.stats.get_summary()
        logger.info(
            f"Pipeline Session Summary: Processed {summary['total_frames']} frames in "
            f"{summary['elapsed_seconds']}s (Avg FPS: {summary['average_fps']}, "
            f"Avg Latency: {summary['avg_inference_ms']}ms)"
        )
