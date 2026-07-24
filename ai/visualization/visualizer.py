"""
Visualizer engine for drawing bounding boxes, lane ROIs, vehicle state badges, and per-lane analytics HUD cards.
"""

from pathlib import Path
from typing import List, Dict, Optional
import cv2
import numpy as np

from config.ui import (
    CLASS_COLORS,
    DEFAULT_COLOR,
    BOX_THICKNESS,
    FONT_SCALE,
    FONT_THICKNESS,
    HUD_BG_COLOR,
    HUD_TEXT_COLOR,
)
from ai.detection.detection_types import Detection
from ai.lane.lane_manager import LaneManager, Lane
from ai.analytics.analytics_exporter import LaneStatistics
from ai.utils.statistics import StatisticsTracker
from ai.utils.logger import get_logger

logger = get_logger("Visualizer")


class Visualizer:
    """
    Decoupled rendering engine for annotating frames with tracks, ROIs, and traffic analytics.
    """

    def __init__(self, save_video: bool = True, output_path: Optional[Path] = None):
        self.save_video = save_video
        self.output_path = output_path
        self.video_writer: Optional[cv2.VideoWriter] = None
        self._is_writer_initialized = False

        # Palette for Lane ROI Polygon Outlines
        self.lane_colors = {
            "North": (255, 100, 100),  # Soft Blue
            "South": (100, 255, 100),  # Soft Green
            "East": (100, 200, 255),   # Soft Amber
            "West": (255, 100, 255),   # Soft Purple
        }

    def _init_video_writer(self, frame_shape: tuple, fps: float = 30.0) -> None:
        """Initialize OpenCV VideoWriter."""
        if not self.save_video or not self.output_path:
            return

        height, width = frame_shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.video_writer = cv2.VideoWriter(
            str(self.output_path), fourcc, fps, (width, height)
        )
        self._is_writer_initialized = True
        logger.info(f"Output VideoWriter initialized: '{self.output_path}' ({width}x{height} @ {fps} FPS)")

    def draw(
        self,
        frame: np.ndarray,
        detections: List[Detection],
        lane_manager: Optional[LaneManager] = None,
        lane_stats: Optional[Dict[str, LaneStatistics]] = None,
        stats: Optional[StatisticsTracker] = None,
        source_fps: float = 30.0,
    ) -> np.ndarray:
        """
        Draw annotations, lane ROIs, vehicle state badges, and analytics HUD onto frame.
        """
        annotated_frame = frame.copy()

        # Initialize VideoWriter if configured
        if self.save_video and not self._is_writer_initialized:
            self._init_video_writer(frame.shape, fps=source_fps)

        # 1. Render Lane ROI Polygons
        if lane_manager:
            self._draw_lane_rois(annotated_frame, lane_manager.lanes)

        # 2. Render Detections and Vehicle Badges
        for det in detections:
            self._draw_detection(annotated_frame, det)

        # 3. Render Top Performance HUD Header
        if stats:
            total_live = sum(s.live_count for s in lane_stats.values()) if lane_stats else len(detections)
            self._draw_performance_hud(annotated_frame, total_live, stats)

        # 4. Render Per-Lane Analytics Side Panel Card
        if lane_stats:
            self._draw_analytics_side_panel(annotated_frame, lane_stats)

        # 5. Write to Output Video File
        if self.save_video and self.video_writer is not None:
            self.video_writer.write(annotated_frame)

        return annotated_frame

    def _draw_lane_rois(self, frame: np.ndarray, lanes: Dict[str, Lane]) -> None:
        """Draw semi-transparent lane ROI polygons and lane labels."""
        overlay = frame.copy()

        for lane_name, lane in lanes.items():
            color = self.lane_colors.get(lane_name, (180, 180, 180))
            cv2.fillPoly(overlay, [lane.polygon], color)
            cv2.polylines(frame, [lane.polygon], isClosed=True, color=color, thickness=2)

        # Blend semi-transparent fill (alpha = 0.15)
        cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)

    def _draw_detection(self, frame: np.ndarray, det: Detection) -> None:
        """Draw bounding box and state label badge onto frame."""
        x1, y1, x2, y2 = det.bbox
        color = CLASS_COLORS.get(det.class_name.lower(), DEFAULT_COLOR)

        # Draw main bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, BOX_THICKNESS)

        # Badge Label Construction: Class #track_id [Lane] Q:queue_sec
        label_parts = []
        if det.track_id is not None:
            label_parts.append(f"#{det.track_id}")
        label_parts.append(det.class_name.title())
        if det.lane:
            label_parts.append(f"[{det.lane}]")
        if det.queue_time_sec > 0:
            label_parts.append(f"Q:{det.queue_time_sec:.1f}s")
        else:
            label_parts.append(f"({det.confidence:.2f})")

        label = " ".join(label_parts)

        # Calculate text size
        (text_width, text_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE * 0.85, FONT_THICKNESS
        )

        badge_y1 = max(0, y1 - text_height - baseline - 6)
        badge_y2 = max(text_height + baseline + 6, y1)

        # Draw background badge rectangle
        cv2.rectangle(
            frame,
            (x1, badge_y1),
            (x1 + text_width + 8, badge_y2),
            color,
            -1,
        )

        # Draw text label
        cv2.putText(
            frame,
            label,
            (x1 + 4, badge_y2 - baseline - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            FONT_SCALE * 0.85,
            (0, 0, 0) if sum(color) > 400 else (255, 255, 255),
            FONT_THICKNESS,
            cv2.LINE_AA,
        )

    def _draw_performance_hud(self, frame: np.ndarray, vehicle_count: int, stats: StatisticsTracker) -> None:
        """Draw top performance header bar."""
        height, width = frame.shape[:2]
        hud_height = 38
        hud_overlay = frame[0:hud_height, 0:width].copy()

        cv2.rectangle(hud_overlay, (0, 0), (width, hud_height), HUD_BG_COLOR, -1)
        cv2.addWeighted(hud_overlay, 0.80, frame[0:hud_height, 0:width], 0.20, 0, frame[0:hud_height, 0:width])

        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.5
        thick = 1

        cv2.putText(frame, f"FPS: {stats.average_fps:.1f}", (15, 24), font, scale, (0, 255, 0), thick, cv2.LINE_AA)
        cv2.putText(frame, f"Inference: {stats.average_inference_time_ms:.1f} ms", (130, 24), font, scale, (0, 215, 255), thick, cv2.LINE_AA)
        cv2.putText(frame, f"Live Vehicles: {vehicle_count}", (330, 24), font, scale, HUD_TEXT_COLOR, thick, cv2.LINE_AA)
        cv2.putText(frame, f"Frame #{stats.frame_count}", (width - 150, 24), font, scale, (200, 200, 200), thick, cv2.LINE_AA)

    def _draw_analytics_side_panel(self, frame: np.ndarray, lane_stats: Dict[str, LaneStatistics]) -> None:
        """Draw right-side Per-Lane Traffic Analytics HUD Card."""
        height, width = frame.shape[:2]
        panel_w = 320
        panel_h = 240
        panel_x = width - panel_w - 15
        panel_y = 50

        # Draw dark glassmorphism container panel
        panel_overlay = frame[panel_y:panel_y + panel_h, panel_x:panel_x + panel_w].copy()
        cv2.rectangle(panel_overlay, (0, 0), (panel_w, panel_h), (20, 20, 20), -1)
        cv2.addWeighted(panel_overlay, 0.80, frame[panel_y:panel_y + panel_h, panel_x:panel_x + panel_w], 0.20, 0, frame[panel_y:panel_y + panel_h, panel_x:panel_x + panel_w])
        cv2.rectangle(frame, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), (0, 255, 204), 1)

        # Header Title
        cv2.putText(frame, "TRAFFIC ANALYTICS (SPRINT 2)", (panel_x + 15, panel_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 204), 1, cv2.LINE_AA)
        cv2.line(frame, (panel_x + 15, panel_y + 32), (panel_x + panel_w - 15, panel_y + 32), (60, 60, 60), 1)

        # Table Column Headers
        y_offset = panel_y + 50
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.40

        cv2.putText(frame, "LANE", (panel_x + 15, y_offset), font, scale, (180, 180, 180), 1)
        cv2.putText(frame, "LIVE/PCE", (panel_x + 85, y_offset), font, scale, (180, 180, 180), 1)
        cv2.putText(frame, "QUEUE", (panel_x + 165, y_offset), font, scale, (180, 180, 180), 1)
        cv2.putText(frame, "STATUS", (panel_x + 235, y_offset), font, scale, (180, 180, 180), 1)

        y_offset += 20
        density_colors = {
            "LOW": (0, 255, 0),
            "MEDIUM": (0, 215, 255),
            "HIGH": (0, 140, 255),
            "CONGESTED": (0, 0, 255),
        }

        for lane_name, stats in lane_stats.items():
            color = density_colors.get(stats.density, (200, 200, 200))

            cv2.putText(frame, f"{lane_name[:5]}", (panel_x + 15, y_offset), font, scale, (255, 255, 255), 1)
            cv2.putText(frame, f"{stats.live_count} ({stats.pce_score:.1f})", (panel_x + 85, y_offset), font, scale, (255, 255, 255), 1)
            cv2.putText(frame, f"{stats.total_queue_time_sec:.1f}s", (panel_x + 165, y_offset), font, scale, (255, 255, 255), 1)
            cv2.putText(frame, f"{stats.density}", (panel_x + 235, y_offset), font, scale, color, 1)

            y_offset += 22

        # Summary line
        cv2.line(frame, (panel_x + 15, y_offset - 5), (panel_x + panel_w - 15, y_offset - 5), (60, 60, 60), 1)
        total_pce = sum(s.pce_score for s in lane_stats.values())
        cv2.putText(frame, f"Total Junction PCE Load: {total_pce:.1f}", (panel_x + 15, y_offset + 12), font, scale, (0, 255, 204), 1)

    def release(self) -> None:
        """Release VideoWriter resources."""
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
            logger.info("VideoWriter released successfully.")
