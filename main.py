"""
Smart Traffic Management System Entry Point
Main execution script for video ingestion, YOLO detection, ByteTrack tracking, lane management,
traffic analytics, adaptive signal decision engine, and performance HUD rendering.
"""

import sys
import time
import cv2
from pathlib import Path

from config.paths import DEFAULT_VIDEO_PATH
from config.ui import WINDOW_NAME
from ai.pipeline.traffic_pipeline import TrafficPipeline
from ai.pipeline.pipeline_result import PipelineResult
from ai.utils.logger import get_logger
from videos.generate_sample_video import generate_synthetic_traffic_video

logger = get_logger("Main")


def main():
    """
    Main application loop for Smart Traffic Management System.
    """
    logger.info("==================================================")
    logger.info("       Smart Traffic Management System           ")
    logger.info(" AI Perception + Analytics + Adaptive Signal Engine")
    logger.info("==================================================")

    # Ensure input video exists; if missing, generate a sample synthetic video
    video_path = DEFAULT_VIDEO_PATH
    if not video_path.exists():
        logger.warning(f"Video file not found at '{video_path}'. Generating sample video...")
        video_path = generate_synthetic_traffic_video()

    # Initialize Pipeline
    pipeline = None
    try:
        pipeline = TrafficPipeline(video_source=video_path, save_output=True)
    except Exception as e:
        logger.error(f"Failed to initialize Traffic Pipeline: {e}", exc_info=True)
        sys.exit(1)

    logger.info(f"Starting video processing. Press 'q' in the window to exit.")

    # OpenCV Display Window
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 1280, 720)

    last_log_time = time.time()
    frame_counter = 0

    try:
        while True:
            # Process single step in pipeline, returning a strongly-typed PipelineResult
            res: PipelineResult = pipeline.process_step()
            
            if not res.has_frame or res.annotated_frame is None:
                logger.info("Video playback completed.")
                break

            frame_counter += 1

            # Concise 1-second status log summary
            current_time = time.time()
            if current_time - last_log_time >= 1.0:
                last_log_time = current_time
                green_str = str(res.signal_decision.green_lane) if res.signal_decision else "None"
                total_vehicles = sum(s.live_count for s in res.lane_stats.values()) if res.lane_stats else len(res.detections)
                
                logger.info(
                    f"Frame #{frame_counter} | Live Vehicles: {total_vehicles} | "
                    f"Active Green: '{green_str}' ({res.remaining_green_sec}s remaining) | "
                    f"Phase Changed: {res.is_phase_change}"
                )

            # Render frame to OpenCV GUI window
            cv2.imshow(WINDOW_NAME, res.annotated_frame)

            # Check for user input: exit when 'q' key is pressed or window closed
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                logger.info("User requested exit (pressed 'q').")
                break

            # Stop if window close button was clicked
            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                logger.info("Window closed by user.")
                break

    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user (Ctrl+C).")
    except Exception as e:
        logger.error(f"Unhandled error during frame execution: {e}", exc_info=True)
    finally:
        # Cleanup pipeline resources
        if pipeline:
            pipeline.release()
        cv2.destroyAllWindows()
        logger.info("Clean shutdown complete.")


if __name__ == "__main__":
    main()
