"""
TrafficPipeline orchestrates full execution flow across Perception, Traffic Analytics, and Signal Decision layers.
Returns strongly-typed PipelineResult objects to eliminate tuple-unpacking issues.
"""

from pathlib import Path
from typing import Optional, Union, Dict, Any
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

        # 4. Video Recording Output Path
        if save_output and output_path is None:
            output_path = get_timestamped_output_path(prefix="traffic_system")

        # 5. Visualizer Renderer
        self.visualizer = Visualizer(save_video=save_output, output_path=output_path)

        # 6. Performance Statistics Monitor
        self.stats = StatisticsTracker()

        logger.info("Smart Traffic Management System Pipeline fully initialized and ready!")

    def process_step(self) -> PipelineResult:
        """
        Execute one step of the pipeline for a single frame.
        
        Returns:
            PipelineResult: Strongly-typed container holding all step outputs.
        """
        success, frame, frame_num, timestamp = self.camera_manager.get_frame()
        if not success or frame is None:
            return PipelineResult(has_frame=False)

        # 1. Perception: YOLO Detection
        raw_detections, inference_ms = self.detector.detect(
            frame, frame_number=frame_num, timestamp=timestamp
        )

        # 2. Perception: ByteTrack Vehicle Tracking
        tracked_detections = self.tracker.update(
            raw_detections, frame=frame, frame_number=frame_num, timestamp=timestamp
        )

        # 3. Analytics: Lane Assignment
        lane_detections = self.lane_manager.assign_lanes(tracked_detections)

        # 4. Analytics: Vehicle State & Motion Tracking
        enriched_detections = self.state_manager.update(
            lane_detections, frame_number=frame_num, timestamp=timestamp
        )

        # 5. Analytics: LaneStatistics Generation
        lane_stats = self.analytics_exporter.generate_stats(self.state_manager)

        # 6. Signal Decision: Compute Base Priority Scores
        base_priority_result = self.priority_calculator.calculate(lane_stats)

        # 7. Signal Decision: Apply Starvation Fairness Bonuses
        fairness_priority_result = self.fairness_manager.apply_fairness(base_priority_result)

        # 8. Signal Decision: Emergency Vehicle Priority Override
        final_priority_result = self.emergency_override.check_and_override(
            fairness_priority_result, lane_stats
        )

        # 9. Signal Decision: Adaptive Green Phase Scheduling
        signal_decision = self.signal_scheduler.schedule(final_priority_result)

        # Update FairnessManager served lane state
        self.fairness_manager.update_served(signal_decision.green_lane)

        # 10. Hardware Command Generation (ESP32 Ready)
        hardware_cmd = self.signal_controller.generate_command(signal_decision)

        # 11. Record Performance Metrics
        self.stats.record_frame(inference_ms)

        # 12. Render Frame Annotations, ROIs, Badges, and Analytics HUD Panel
        annotated_frame = self.visualizer.draw(
            frame=frame,
            detections=enriched_detections,
            lane_manager=self.lane_manager,
            lane_stats=lane_stats,
            stats=self.stats,
            source_fps=self.camera_manager.fps,
        )

        # Log periodic progress
        if frame_num % 100 == 0:
            active_cnt = sum(s.live_count for s in lane_stats.values())
            logger.info(
                f"Frame #{frame_num} | Active Vehicles: {active_cnt} | "
                f"Scheduled Green: '{signal_decision.green_lane}' ({signal_decision.green_duration_sec}s) | "
                f"FPS: {self.stats.average_fps:.1f} | Latency: {self.stats.average_inference_time_ms:.1f}ms"
            )

        return PipelineResult(
            has_frame=True,
            annotated_frame=annotated_frame,
            detections=enriched_detections,
            lane_stats=lane_stats,
            priority_result=final_priority_result,
            signal_decision=signal_decision,
            hardware_command=hardware_cmd,
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
