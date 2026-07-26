"""
Smart Traffic Management System — Production AI Traffic Controller Entry Point.
Orchestrates Startup Wizard (StartupConfig / ProfileManager), Multi-Camera Ingestion (CameraManager),
Multi-Camera AI Pipeline (TrafficPipeline), and Post-Decision Control Layer (ControlManager -> Logger, ESP32, Dashboard).
"""

import sys
import time
import cv2

from config.ui import WINDOW_NAME
from startup import StartupManager, StartupConfig
from ai.camera import CameraManager
from ai.pipeline.traffic_pipeline import TrafficPipeline
from ai.pipeline.pipeline_result import PipelineResult
from ai.controller.control_manager import ControlManager
from ai.utils.logger import get_logger

logger = get_logger("Main")


def main():
    """
    Main application entry point for Smart Traffic Management System.
    """
    # 1. Startup Setup Wizard (CLI Prompting, Validation & Profile Management)
    startup_cfg: StartupConfig = StartupManager.run(interactive=True)

    cam_sources = startup_cfg.camera.to_stream_config()
    hw_port = startup_cfg.hardware.port
    is_sim = startup_cfg.hardware.simulation

    logger.info(f"Initializing CameraManager with mode '{startup_cfg.camera.mode.upper()}'...")
    logger.info(f"Initializing ESP32 Hardware Interface on port '{hw_port}' (Simulation={is_sim})...")

    pipeline = None
    control_manager = None
    try:
        # 2. Camera Acquisition Layer
        camera_manager = CameraManager(config=cam_sources)

        # 3. Control Layer & Hardware Interface
        control_manager = ControlManager(esp32_port=hw_port, simulation_mode=is_sim)

        # 4. Perception & Decision Engine Pipeline
        pipeline = TrafficPipeline(camera_manager=camera_manager, save_output=True)
    except Exception as e:
        logger.error(f"Failed to initialize Traffic Controller subsystems: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Starting Production Traffic Control System. Press 'q' in dashboard window to exit.")

    # OpenCV GUI Display Window
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 1280, 870)

    last_log_time = time.time()
    frame_counter = 0

    try:
        while True:
            # Step 1: Perception & Decision Engine step -> returns PipelineResult
            res: PipelineResult = pipeline.process_step()

            if not res.has_frame:
                logger.info("Camera stream ingestion completed.")
                break

            frame_counter += 1

            # Step 2: Control Layer -> handles CSV/JSONL logging, ESP32 hardware transmission, and renders Dashboard
            dashboard_frame = control_manager.process_result(res)

            # Step 3: Periodic 1-second status log summary
            current_time = time.time()
            if current_time - last_log_time >= 1.0:
                last_log_time = current_time
                green_str = str(res.signal_decision.green_lane).upper() if res.signal_decision else "NONE"
                total_vehicles = res.intersection_state.total_vehicles if res.intersection_state else 0
                hw_status = control_manager.esp32_interface.get_status()
                hw_mode = "SIMULATED" if hw_status.simulation_mode else "HARDWARE"

                logger.info(
                    f"Frame #{frame_counter} | Active Green: '{green_str}' ({res.remaining_green_sec}s left) | "
                    f"Vehicles: {total_vehicles} | ESP32 Mode: {hw_mode} | Phase Changed: {res.is_phase_change}"
                )

            # Step 4: Render to OpenCV GUI display window
            cv2.imshow(WINDOW_NAME, dashboard_frame)

            # Check key press (exit on 'q')
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                logger.info("User requested exit (pressed 'q').")
                break

            # Stop if window close button was clicked
            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                logger.info("Window closed by user.")
                break

    except KeyboardInterrupt:
        logger.info("Traffic System interrupted by user (Ctrl+C).")
    except Exception as e:
        logger.error(f"Unhandled error during execution loop: {e}", exc_info=True)
    finally:
        # Resource cleanup
        if pipeline:
            pipeline.release()
        if control_manager:
            control_manager.release()
        cv2.destroyAllWindows()
        logger.info("Clean shutdown complete.")


if __name__ == "__main__":
    main()
