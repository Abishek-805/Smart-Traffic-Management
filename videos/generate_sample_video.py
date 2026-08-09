"""
Utility script to generate a synthetic traffic video with moving cars, buses, and trucks for testing.
"""

import sys
from pathlib import Path

# Add project root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import cv2
import numpy as np

from config.paths import DEFAULT_VIDEO_PATH, VIDEOS_DIR
from ai.utils.logger import get_logger

logger = get_logger("GenerateSampleVideo")


def generate_synthetic_traffic_video(
    output_path: Path = DEFAULT_VIDEO_PATH,
    width: int = 1280,
    height: int = 720,
    fps: int = 30,
    duration_sec: int = 10,
    title: str = "DEFAULT TRAFFIC FEED",
) -> Path:
    """
    Generates a realistic synthetic road scene with moving vehicle shapes.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    total_frames = fps * duration_sec
    logger.info(f"Generating synthetic traffic video '{output_path.name}' ({width}x{height} @ {fps} FPS)...")

    # Define vehicle objects (x, y, speed, width, height, color, label)
    vehicles = [
        {"x": 100, "y": 300, "speed": 6, "w": 120, "h": 60, "color": (50, 50, 220), "type": "Car"},
        {"x": 400, "y": 350, "speed": 4, "w": 220, "h": 80, "color": (50, 180, 50), "type": "Bus"},
        {"x": 800, "y": 420, "speed": 8, "w": 100, "h": 50, "color": (220, 100, 50), "type": "Car"},
        {"x": 200, "y": 500, "speed": 5, "w": 250, "h": 90, "color": (200, 50, 200), "type": "Truck"},
        {"x": 950, "y": 550, "speed": 7, "w": 70, "h": 40, "color": (0, 200, 250), "type": "Motorcycle"},
    ]

    for frame_idx in range(total_frames):
        # Create road backdrop
        frame = np.ones((height, width, 3), dtype=np.uint8) * 40  # Dark asphalt gray

        # Draw road lane markings
        cv2.rectangle(frame, (0, 250), (width, 650), (60, 60, 60), -1)
        
        # Lane divider dashes
        dash_offset = (frame_idx * 5) % 80
        for y_lane in [380, 480]:
            for x_dash in range(-100 + dash_offset, width + 100, 80):
                cv2.line(frame, (x_dash, y_lane), (x_dash + 40, y_lane), (255, 255, 255), 3)

        # Draw moving vehicles
        for veh in vehicles:
            veh["x"] = (veh["x"] + veh["speed"]) % (width + 300)
            x_pos = veh["x"] - 200
            
            # Vehicle body
            cv2.rectangle(
                frame,
                (int(x_pos), veh["y"]),
                (int(x_pos + veh["w"]), veh["y"] + veh["h"]),
                veh["color"],
                -1,
            )
            # Vehicle roof/windshield block
            roof_w = int(veh["w"] * 0.5)
            roof_h = int(veh["h"] * 0.4)
            roof_x = int(x_pos + (veh["w"] - roof_w) / 2)
            roof_y = veh["y"] - roof_h
            cv2.rectangle(
                frame,
                (roof_x, roof_y),
                (roof_x + roof_w, veh["y"]),
                (veh["color"][0] // 2, veh["color"][1] // 2, veh["color"][2] // 2),
                -1,
            )
            # Wheels
            for wheel_x in [x_pos + 20, x_pos + veh["w"] - 30]:
                cv2.circle(frame, (int(wheel_x), veh["y"] + veh["h"]), 10, (10, 10, 10), -1)

        # Header title banner
        cv2.rectangle(frame, (0, 0), (width, 50), (20, 20, 20), -1)
        cv2.putText(frame, title, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 220, 255), 2, cv2.LINE_AA)

        out.write(frame)

    out.release()
    logger.info(f"Synthetic video successfully saved to: '{output_path}'")
    return output_path


def generate_all_directional_videos(duration_sec: int = 10) -> None:
    """
    Generate synthetic sample videos for North, South, East, and West cameras.
    """
    cameras = [
        ("north.mp4", "NORTH APPROACH - CAM 01"),
        ("south.mp4", "SOUTH APPROACH - CAM 02"),
        ("east.mp4", "EAST APPROACH - CAM 03"),
        ("west.mp4", "WEST APPROACH - CAM 04"),
        ("traffic.mp4", "MAIN TRAFFIC INTERSECTION"),
    ]
    for filename, title in cameras:
        path = VIDEOS_DIR / filename
        generate_synthetic_traffic_video(output_path=path, duration_sec=duration_sec, title=title)


if __name__ == "__main__":
    generate_all_directional_videos()

