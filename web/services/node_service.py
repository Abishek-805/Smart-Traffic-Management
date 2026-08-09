"""
NodeService manages mobile camera node queries, Signal Quality metrics, and QR code pairing.
"""

import base64
import io
import time
from typing import Dict, Any, List
from core.application_context import ApplicationContext
from ai.utils.logger import get_logger

logger = get_logger("NodeService")


import socket

def get_local_ip() -> str:
    """Dynamically get the host machine's active LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "192.168.1.3"


class NodeService:
    """
    Service layer handling camera node sessions and QR code generation.
    """

    def __init__(self, ctx: ApplicationContext = None):
        self.ctx = ctx or ApplicationContext.get_instance()

    def get_connected_nodes(self) -> Dict[str, Any]:
        """Return connected mobile node sessions with calculated Signal Quality."""
        sessions = self.ctx.session_manager.sessions
        all_directions = ["north", "south", "east", "west"]
        connected_by_dir = {sess.camera_direction.lower(): (nid, sess) for nid, sess in sessions.items()}
        node_list = []

        for direction in all_directions:
            if direction in connected_by_dir:
                nid, sess = connected_by_dir[direction]
                latency = 24  # ms
                sig_quality = "Excellent" if latency < 40 else ("Good" if latency < 100 else "Weak")
                node_list.append({
                    "node_id": nid,
                    "assigned_lane": f"{direction.capitalize()} Approach - Lane 1",
                    "device_name": f"Mobile Node ({direction.capitalize()})",
                    "signal_quality": sig_quality,
                    "battery_pct": 84,
                    "latency_ms": latency,
                    "resolution": "1280x720 @ 30 FPS",
                    "status": "CONNECTED",
                    "last_heartbeat": "Just now",
                })
            else:
                pairing_sess = self.ctx.session_manager.get_pairing_session(direction)
                if pairing_sess:
                    expires_at = pairing_sess["expires_at"]
                    time_remaining = max(0, int(expires_at - time.time()))
                    node_list.append({
                        "node_id": pairing_sess["session_id"],
                        "assigned_lane": f"{direction.capitalize()} Approach - Pairing",
                        "device_name": "Pairing Session Active",
                        "signal_quality": "N/A",
                        "battery_pct": 0,
                        "latency_ms": 0,
                        "resolution": "Offline",
                        "status": "PAIRED",
                        "last_heartbeat": f"{time_remaining}s remaining",
                        "expires_at": int(expires_at * 1000),
                    })
                else:
                    node_list.append({
                        "node_id": f"SLOT-{direction.upper()}",
                        "assigned_lane": f"{direction.capitalize()} Approach - Unpaired",
                        "device_name": "No Device Paired",
                        "signal_quality": "N/A",
                        "battery_pct": 0,
                        "latency_ms": 0,
                        "resolution": "Offline",
                        "status": "OFFLINE",
                        "last_heartbeat": "Unregistered",
                    })

        return {
            "connected_count": len([n for n in node_list if n["status"] == "CONNECTED"]),
            "nodes": node_list,
        }

    def generate_qr_payload_and_image(self, direction: str = "north") -> Dict[str, Any]:
        """
        Generate pairing QR payload JSON and base64 PNG QR image data URI for a specific camera approach direction.
        """
        dir_clean = (direction or "north").lower()
        host_ip = get_local_ip()
        expires_at = time.time() + 300
        session_id = f"CAM-{dir_clean.upper()}-PAIR"
        token_val = f"auth_token_{dir_clean}_9df7c6ab"

        self.ctx.session_manager.register_pairing_session(dir_clean, session_id, expires_at)

        qr_payload = {
            "version": "1.0",
            "server": host_ip,
            "port": 8000,
            "session": session_id,
            "token": token_val,
            "expires": int(expires_at * 1000),
            "protocol": "websocket",
            "secure": False,
            "defaultLane": f"{dir_clean.capitalize()} Intersection - Lane 1",
            "camera_direction": dir_clean,
        }

        base64_qr = ""
        try:
            import qrcode
            import json
            img = qrcode.make(json.dumps(qr_payload))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            base64_qr = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception:
            base64_qr = f"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><rect width='100%' height='100%' fill='white'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' fill='black' font-size='14'>QR ({dir_clean.upper()}): {host_ip}:8000</text></svg>"

        return {
            "payload": qr_payload,
            "qr_image": base64_qr,
        }

