"""
MultiCameraDashboard visualizer rendering multi-stream video feeds, perception overlays,
telemetry badges, placeholder frames for offline streams, and Signal Control Engine HUD.
"""

import math
import time
from typing import Dict, Any, Tuple, Optional
from typing import Dict, Any, Tuple, Optional, List
import cv2
import numpy as np


class MultiCameraDashboard:
    """
    Renders multi-camera stream feeds in a dynamic grid layout with perception telemetry,
    hardware interface status, decision history, and health monitoring.
    """

    def __init__(self, tile_width: int = 640, tile_height: int = 360):
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.header_height = 50
        self.status_bar_height = 140  # Expanded height to accommodate ESP32 status & Decision History

    def render_from_result(
        self,
        result: Any,
        hardware_status: Optional[Any] = None,
        decision_history: Optional[List[str]] = None,
    ) -> np.ndarray:
        """
        Render composite multi-camera control dashboard downstream directly from a PipelineResult payload.
        """
        if not getattr(result, "has_frame", False):
            return self._create_empty_dashboard("NO PIPELINE FRAME")

        lane_results = getattr(result, "lane_results", {})
        stream_data = {}

        if lane_results:
            for lane_name, lane_res in lane_results.items():
                ann_frame = getattr(lane_res, "annotated_frame", None)
                raw_frame = getattr(lane_res, "raw_frame", None)
                target_frame = ann_frame if ann_frame is not None else raw_frame
                stream_data[lane_name] = {
                    "frame": target_frame,
                    "connected": getattr(lane_res, "connected", True),
                    "fps": getattr(lane_res, "fps", 30.0),
                    "timestamp": getattr(lane_res, "timestamp", time.time()),
                }
        else:
            multi_frames = getattr(result, "multi_annotated_frames", {})
            for lane_name, frame in multi_frames.items():
                stream_data[lane_name] = {"frame": frame, "connected": True, "fps": 30.0}

        intersection_state = getattr(result, "intersection_state", None)
        if intersection_state and hasattr(intersection_state, "lanes"):
            lanes_map = intersection_state.lanes
        else:
            lanes_map = getattr(result, "lane_stats", {})

        return self.render(
            stream_data=stream_data,
            intersection_state=lanes_map,
            signal_decision=getattr(result, "signal_decision", None),
            remaining_green_sec=getattr(result, "remaining_green_sec", 0),
            hardware_status=hardware_status,
            decision_history=decision_history,
        )

    def render(
        self,
        stream_data: Dict[str, Dict[str, Any]],
        intersection_state: Optional[Dict[str, Any]] = None,
        signal_decision: Optional[Any] = None,
        remaining_green_sec: int = 0,
        hardware_status: Optional[Any] = None,
        decision_history: Optional[List[str]] = None,
    ) -> np.ndarray:
        """
        Renders a composite dashboard image from multi-camera stream payloads and decision engine telemetry.

        Args:
            stream_data: Dictionary mapping camera lane names to frame + metadata dictionaries.
            intersection_state: Optional map of lane_name -> LaneStatistics.
            signal_decision: Optional active SignalDecision object.
            remaining_green_sec: Active phase remaining time in seconds.

        Returns:
            np.ndarray: Unified OpenCV display frame composite.
        """
        num_cameras = len(stream_data)
        if num_cameras == 0:
            return self._create_empty_dashboard("NO CAMERA STREAMS CONFIGURED")

        # Determine dynamic grid dimensions (cols, rows)
        cols = 2 if num_cameras <= 4 else math.ceil(math.sqrt(num_cameras))
        rows = math.ceil(num_cameras / cols)

        grid_width = cols * self.tile_width

        # Create tile images for each stream
        tiles = []
        for lane_name, meta in stream_data.items():
            lane_stats = intersection_state.get(lane_name) if intersection_state else None
            tile = self._render_camera_tile(lane_name, meta, lane_stats)
            tiles.append(tile)

        # Pad remaining grid cells with blank tiles if needed
        total_cells = cols * rows
        while len(tiles) < total_cells:
            tiles.append(self._create_placeholder_tile("STANDBY", connected=False))

        # Assemble grid rows
        row_images = []
        for r in range(rows):
            row_tiles = tiles[r * cols : (r + 1) * cols]
            row_img = np.hstack(row_tiles)
            row_images.append(row_img)

        grid_composite = np.vstack(row_images)

        # Render Header & Footer Control Panel
        header = self._render_dashboard_header(grid_width, num_cameras)
        status_bar = self._render_signal_and_health_panel(
            grid_width, stream_data, signal_decision, remaining_green_sec, hardware_status, decision_history
        )

        # Combine Header, Grid, and Control Panel
        full_dashboard = np.vstack([header, grid_composite, status_bar])
        return full_dashboard

    def _render_camera_tile(
        self,
        lane_name: str,
        meta: Dict[str, Any],
        lane_stats: Optional[Any] = None,
    ) -> np.ndarray:
        """Render individual camera tile frame with perception HUD and telemetry overlays."""
        frame = meta.get("frame")
        connected = meta.get("connected", False)
        fps = meta.get("fps", 0.0)
        resolution = meta.get("resolution", (0, 0))
        frame_num = meta.get("frame_number", 0)

        display_name = lane_name.upper()

        if not connected or frame is None:
            return self._create_placeholder_tile(display_name, connected=False)

        # Resize frame to standard tile resolution
        tile = cv2.resize(frame, (self.tile_width, self.tile_height))

        # Top Banner Overlay
        cv2.rectangle(tile, (0, 0), (self.tile_width, 40), (15, 15, 15), -1)
        
        # Camera Name Title
        cv2.putText(
            tile,
            f"CAMERA: {display_name}",
            (15, 26),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        # Status Badge (Green "✓ Connected")
        status_text = "CONNECTED"
        cv2.rectangle(
            tile,
            (self.tile_width - 130, 8),
            (self.tile_width - 10, 32),
            (30, 120, 30),
            -1,
        )
        cv2.putText(
            tile,
            status_text,
            (self.tile_width - 122, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        # Telemetry HUD Overlay (Live Vehicles, Queue, PCE)
        cv2.rectangle(
            tile,
            (0, self.tile_height - 35),
            (self.tile_width, self.tile_height),
            (10, 10, 10),
            -1,
        )

        if lane_stats:
            v_count = getattr(lane_stats, "live_count", 0)
            q_sec = getattr(lane_stats, "total_queue_time_sec", 0.0)
            pce = getattr(lane_stats, "pce_score", 0.0)
            hud_info = f"Vehicles: {v_count}  |  Queue: {q_sec:.1f}s  |  PCE: {pce:.1f}  |  FPS: {fps:.1f}"
            hud_color = (0, 255, 204) if v_count > 0 else (200, 200, 200)
        else:
            hud_info = f"FPS: {fps:.1f}  |  Res: {resolution[0]}x{resolution[1]}  |  Frame: #{frame_num}"
            hud_color = (200, 200, 200)

        cv2.putText(
            tile,
            hud_info,
            (15, self.tile_height - 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            hud_color,
            1,
            cv2.LINE_AA,
        )

        # Tile border outline
        cv2.rectangle(tile, (0, 0), (self.tile_width - 1, self.tile_height - 1), (60, 60, 60), 2)
        return tile

    def _create_placeholder_tile(self, label: str, connected: bool = False) -> np.ndarray:
        """Create placeholder display tile for disconnected/standby cameras."""
        tile = np.ones((self.tile_height, self.tile_width, 3), dtype=np.uint8) * 25

        # Draw dark hash patterns for signal loss effect
        for y in range(0, self.tile_height, 40):
            cv2.line(tile, (0, y), (self.tile_width, y + 20), (35, 35, 35), 1)

        # Top Header
        cv2.rectangle(tile, (0, 0), (self.tile_width, 40), (15, 15, 15), -1)
        cv2.putText(
            tile,
            f"CAMERA: {label.upper()}",
            (15, 26),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (180, 180, 180),
            2,
            cv2.LINE_AA,
        )

        # Disconnected Badge
        cv2.rectangle(
            tile,
            (self.tile_width - 145, 8),
            (self.tile_width - 10, 32),
            (30, 30, 160),
            -1,
        )
        cv2.putText(
            tile,
            "DISCONNECTED",
            (self.tile_width - 140, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        # Center Warning Text
        center_x = self.tile_width // 2
        center_y = self.tile_height // 2
        cv2.putText(
            tile,
            "NO SIGNAL / OFFLINE",
            (center_x - 110, center_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (80, 80, 220),
            2,
            cv2.LINE_AA,
        )

        cv2.rectangle(tile, (0, 0), (self.tile_width - 1, self.tile_height - 1), (50, 50, 120), 2)
        return tile

    def _render_dashboard_header(self, width: int, num_cameras: int) -> np.ndarray:
        """Render top dashboard header bar."""
        header = np.zeros((self.header_height, width, 3), dtype=np.uint8)
        cv2.rectangle(header, (0, 0), (width, self.header_height), (30, 30, 30), -1)
        
        cv2.putText(
            header,
            "SMART TRAFFIC SYSTEM — MULTI-CAMERA CONTROL DASHBOARD",
            (20, 33),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 220, 255),
            2,
            cv2.LINE_AA,
        )

        ts_str = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(
            header,
            f"FEEDS: {num_cameras}  |  {ts_str}",
            (width - 320, 33),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (200, 200, 200),
            1,
            cv2.LINE_AA,
        )
        cv2.line(header, (0, self.header_height - 1), (width, self.header_height - 1), (0, 180, 220), 2)
        return header

    def _render_signal_and_health_panel(
        self,
        width: int,
        stream_data: Dict[str, Dict[str, Any]],
        signal_decision: Optional[Any],
        remaining_green_sec: int,
        hardware_status: Optional[Any] = None,
        decision_history: Optional[List[str]] = None,
    ) -> np.ndarray:
        """Render bottom panel displaying Signal Engine State, Hardware Status, Decision History, and Camera Health Monitor."""
        panel = np.zeros((self.status_bar_height, width, 3), dtype=np.uint8)
        cv2.rectangle(panel, (0, 0), (width, self.status_bar_height), (20, 20, 20), -1)
        cv2.line(panel, (0, 0), (width, 0), (60, 60, 60), 2)

        font = cv2.FONT_HERSHEY_SIMPLEX

        # Row 1: Signal Control Engine Status
        if signal_decision:
            phase_id = getattr(signal_decision, "phase_id", 1)
            green_lane = str(getattr(signal_decision, "green_lane", "NORTH")).upper()
            reason = getattr(signal_decision, "reason_details", "Optimal Priority")

            # Phase & Green Lane Box
            cv2.rectangle(panel, (15, 10), (320, 48), (0, 140, 0), -1)
            cv2.putText(
                panel,
                f"GREEN LANE: {green_lane} (Phase #{phase_id})",
                (25, 34),
                font,
                0.55,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            # Timer Box
            cv2.rectangle(panel, (335, 10), (480, 48), (0, 180, 220), -1)
            cv2.putText(
                panel,
                f"TIMER: {remaining_green_sec}s",
                (345, 34),
                font,
                0.55,
                (0, 0, 0),
                2,
                cv2.LINE_AA,
            )

            # Decision Reason
            cv2.putText(
                panel,
                f"Reason: {reason[:42]}",
                (495, 34),
                font,
                0.48,
                (220, 220, 220),
                1,
                cv2.LINE_AA,
            )
        else:
            cv2.putText(
                panel,
                "SIGNAL ENGINE: INITIALIZING PHASE SCHEDULER...",
                (20, 34),
                font,
                0.55,
                (0, 215, 255),
                2,
                cv2.LINE_AA,
            )

        # Row 2: Pipeline Health & Hardware Connection Status
        cv2.line(panel, (15, 58), (width - 15, 58), (50, 50, 50), 1)

        # Pipeline Health badge
        cv2.putText(panel, "Pipeline: HEALTHY", (15, 80), font, 0.48, (0, 255, 0), 1, cv2.LINE_AA)

        # ESP32 Hardware Status telemetry badge
        if hardware_status:
            is_sim = getattr(hardware_status, "simulation_mode", True)
            is_conn = getattr(hardware_status, "connected", False)
            port_name = getattr(hardware_status, "port", "SIMULATED")
            if is_conn and not is_sim:
                hw_str = f"ESP32: CONNECTED ({port_name})"
                hw_color = (0, 255, 0)
            else:
                hw_str = f"ESP32: SIMULATED ({port_name})"
                hw_color = (0, 215, 255)
        else:
            hw_str = "ESP32: SIMULATION MODE"
            hw_color = (0, 215, 255)

        cv2.putText(panel, hw_str, (185, 80), font, 0.48, hw_color, 1, cv2.LINE_AA)

        # Decision History summary text
        if decision_history and len(decision_history) > 0:
            hist_str = f"History: {decision_history[0]}"
            cv2.putText(panel, hist_str[:60], (495, 80), font, 0.45, (180, 220, 255), 1, cv2.LINE_AA)

        # Row 3: Camera Health Monitor
        cv2.line(panel, (15, 96), (width - 15, 96), (50, 50, 50), 1)
        cv2.putText(
            panel,
            "CAMERAS:",
            (15, 122),
            font,
            0.48,
            (180, 180, 180),
            1,
            cv2.LINE_AA,
        )

        num_items = max(1, len(stream_data))
        start_x = 120
        avail_w = width - start_x - 20
        col_w = avail_w // num_items

        for idx, (lane, meta) in enumerate(stream_data.items()):
            connected = meta.get("connected", False)
            x_pos = start_x + idx * col_w

            lane_label = lane.capitalize()
            if connected:
                status_str = f"{lane_label}: Connected"
                color = (50, 220, 50)
            else:
                status_str = f"{lane_label}: Offline"
                color = (50, 50, 240)

            cv2.putText(
                panel,
                status_str,
                (x_pos, 122),
                font,
                0.48,
                color,
                1,
                cv2.LINE_AA,
            )

        return panel

    def _create_empty_dashboard(self, msg: str) -> np.ndarray:
        """Create visual fallback canvas when no streams exist."""
        canvas = np.ones((720, 1280, 3), dtype=np.uint8) * 30
        cv2.putText(canvas, msg, (400, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        return canvas
