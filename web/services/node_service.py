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
import os
import uuid
import ipaddress

import psutil


def _active_windows_hotspot_ip() -> str | None:
    """Return the IPv4 address exposed by an active Windows Mobile Hotspot."""
    try:
        stats = psutil.net_if_stats()
        for name, addresses in psutil.net_if_addrs().items():
            if not name.lower().startswith("local area connection*"):
                continue
            if not stats.get(name) or not stats[name].isup:
                continue
            for address in addresses:
                if address.family != socket.AF_INET:
                    continue
                ip = ipaddress.ip_address(address.address)
                if ip.is_private and not ip.is_link_local and not ip.is_loopback:
                    return address.address
    except (OSError, RuntimeError, ValueError):
        logger.warning("Unable to inspect Windows hotspot adapters; using routed LAN address")
    return None

def get_local_ip() -> str:
    """Dynamically get the host machine's active LAN IP address."""
    hotspot_ip = _active_windows_hotspot_ip()
    if hotspot_ip:
        return hotspot_ip
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


class NodeService:
    """
    Service layer handling camera node sessions and QR code generation.
    """

    def __init__(self, ctx: ApplicationContext = None):
        self.ctx = ctx or ApplicationContext.get_instance()

    def get_connected_nodes(self) -> Dict[str, Any]:
        """Return connected mobile node sessions with calculated Signal Quality."""
        from server.runtime import runtime_snapshot
        payload = ((self.ctx.latest_snapshot or {}).get("payload", {}) if self.ctx.remote_runtime
                   else runtime_snapshot(self.ctx)["payload"])
        nodes = list(self.ctx.remote_nodes if self.ctx.remote_runtime else payload.get("nodes", []))
        for direction in ("north", "east", "south", "west"):
            if any(n.get("assigned_lane", "").lower().startswith(direction) for n in nodes):
                continue
            pairing = self.ctx.session_manager.get_pairing_session(direction)
            nodes.append({"node_id": pairing["session_id"] if pairing else "SLOT-" + direction.upper(),
                          "assigned_lane": direction.capitalize() + " Approach",
                          "device_name": "Awaiting camera" if pairing else "No device connected",
                          "status": "PAIRED" if pairing else "OFFLINE", "fps": 0,
                          "battery_pct": None, "signal_dbm": None, "latency_ms": None,
                          "last_heartbeat": "Awaiting registration",
                          "expires_at": int(pairing["expires_at"] * 1000) if pairing else None})
        return {"connected_count": sum(n["status"] == "LIVE" for n in nodes), "nodes": nodes}

    def generate_qr_payload_and_image(self, direction: str = "north") -> Dict[str, Any]:
        """
        Generate pairing QR payload JSON and base64 PNG QR image data URI for a specific camera approach direction.
        """
        dir_clean = (direction or "north").lower()
        if dir_clean not in ("north", "south", "east", "west"):
            raise ValueError("Invalid direction")
        host_ip = os.getenv("CAMERA_PUBLIC_HOST") or get_local_ip()
        # Combined local runtime is the default. Docker explicitly supplies 8001.
        port = int(os.getenv("CAMERA_WS_PORT", "8000"))
        secure = os.getenv("CAMERA_WS_SECURE", "false").lower() == "true"
        expires_at = time.time() + 300
        session_id = f"CAM-{dir_clean.upper()}-{uuid.uuid4().hex[:8]}"
        token_val = uuid.uuid4().hex

        self.ctx.session_manager.register_pairing_session(dir_clean, session_id, token_val, expires_at)

        qr_payload = {
            "version": "1.0",
            "server": host_ip,
            "port": port,
            "session": session_id,
            "token": token_val,
            "expires": int(expires_at * 1000),
            "protocol": "wss" if secure else "ws",
            "secure": secure,
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
        except Exception as exc:
            raise RuntimeError("QR generation failed; install qrcode and Pillow") from exc

        return {
            "payload": qr_payload,
            "qr_image": base64_qr,
        }

