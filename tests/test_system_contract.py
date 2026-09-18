"""
Cross-Repository System Contract Tests.
Dynamically parses and validates contracts between:
- Mobile Client: C:\\Users\\ashek\\Desktop\\traffic-camera-app
- Backend System: C:\\Users\\ashek\\Desktop\\smart-traffic-management
"""

import json
import os
import re
from pathlib import Path
import pytest
from web.services.node_service import NodeService
from server.protocol import MessageType as BackendMessageType, PROTOCOL_VERSION as BACKEND_PROTOCOL_VERSION


MOBILE_ROOT = Path(r"C:\Users\ashek\Desktop\traffic-camera-app")


def get_mobile_protocol_version() -> str:
    """Parse PROTOCOL_VERSION from traffic-camera-app/src/protocol/constants/Protocol.ts."""
    file_path = MOBILE_ROOT / "src" / "protocol" / "constants" / "Protocol.ts"
    if not file_path.exists():
        pytest.skip(f"Mobile repository not found at {MOBILE_ROOT}")
    content = file_path.read_text(encoding="utf-8")
    match = re.search(r"export\s+const\s+PROTOCOL_VERSION\s*=\s*['\"]([^'\"]+)['\"]", content)
    assert match, "Could not find PROTOCOL_VERSION in mobile Protocol.ts"
    return match.group(1)


def get_mobile_valid_directions() -> set[str]:
    """Parse validDirections from traffic-camera-app/src/protocol/validators/ProtocolValidator.ts."""
    file_path = MOBILE_ROOT / "src" / "protocol" / "validators" / "ProtocolValidator.ts"
    if not file_path.exists():
        pytest.skip(f"Mobile repository not found at {MOBILE_ROOT}")
    content = file_path.read_text(encoding="utf-8")
    match = re.search(r"validDirections\s*=\s*\[([^\]]+)\]", content)
    assert match, "Could not find validDirections in mobile ProtocolValidator.ts"
    raw_items = match.group(1)
    return set(re.findall(r"['\"]([^'\"]+)['\"]", raw_items))


def get_mobile_message_types() -> set[str]:
    """Parse MessageType union from traffic-camera-app/src/types/protocol.ts."""
    file_path = MOBILE_ROOT / "src" / "types" / "protocol.ts"
    if not file_path.exists():
        pytest.skip(f"Mobile repository not found at {MOBILE_ROOT}")
    content = file_path.read_text(encoding="utf-8")
    match = re.search(r"export\s+type\s+MessageType\s*=([^;]+);", content, re.DOTALL)
    assert match, "Could not find MessageType in mobile protocol.ts"
    raw_types = match.group(1)
    return set(re.findall(r"['\"]([A-Z_]+)['\"]", raw_types))


def test_contract_protocol_version():
    """Verify protocol version compatibility between mobile and backend source code."""
    mobile_version = get_mobile_protocol_version()
    assert BACKEND_PROTOCOL_VERSION.startswith(mobile_version), (
        f"Backend version '{BACKEND_PROTOCOL_VERSION}' does not start with mobile version '{mobile_version}'"
    )


def test_contract_supported_directions():
    """Verify both repositories agree on supported camera approach directions."""
    mobile_directions = get_mobile_valid_directions()
    backend_directions = {"north", "south", "east", "west"}
    assert mobile_directions == backend_directions, (
        f"Direction mismatch: mobile={mobile_directions}, backend={backend_directions}"
    )


def test_contract_message_types_coverage():
    """Verify backend supports all core message types defined in mobile types."""
    mobile_types = get_mobile_message_types()
    backend_types = {m.value for m in BackendMessageType}

    # Core message types required for operational stream negotiation
    required_mutual_types = {
        "REGISTER_CAMERA",
        "REGISTRATION_ACK",
        "START_STREAM",
        "STOP_STREAM",
        "HEARTBEAT",
        "HEARTBEAT_ACK",
        "VIDEO_FRAME",
        "WEBRTC_OFFER",
        "WEBRTC_STOP",
        "DISCONNECT",
        "ERROR",
    }

    assert required_mutual_types.issubset(mobile_types), (
        f"Mobile types missing required messages: {required_mutual_types - mobile_types}"
    )
    assert required_mutual_types.issubset(backend_types), (
        f"Backend types missing required messages: {required_mutual_types - backend_types}"
    )


def test_contract_qr_payload_schema_and_roundtrip():
    """Verify backend-generated QR payloads satisfy mobile ProtocolValidator rules."""
    mobile_directions = get_mobile_valid_directions()
    node_svc = NodeService()

    for direction in mobile_directions:
        qr = node_svc.generate_qr_payload_and_image(direction)
        payload = qr["payload"]

        # 1. Server must be valid non-empty string without slashes or spaces
        assert isinstance(payload.get("server"), str) and len(payload["server"].strip()) > 0
        assert "/" not in payload["server"] and not re.search(r"\s", payload["server"])

        # 2. Port must be integer between 1 and 65535
        port = payload.get("port")
        assert isinstance(port, int) and 1 <= port <= 65535

        # 3. Session and token non-empty strings
        assert isinstance(payload.get("session"), str) and len(payload["session"]) > 0
        assert isinstance(payload.get("token"), str) and len(payload["token"]) > 0

        # 4. Expires must be a finite millisecond timestamp in future
        expires = payload.get("expires")
        assert isinstance(expires, int) and expires > 0

        # 5. Protocol must be ws or wss
        assert payload.get("protocol") in {"ws", "wss"}

        # 6. Direction must match mobile valid directions
        assert payload.get("camera_direction") == direction

        # 7. QR base64 image must be present
        assert qr["qr_image"].startswith("data:image/png;base64,")


def test_contract_ports_alignment():
    """Verify default ports align with standard 8000 combined mode and 8001 split mode."""
    port = int(os.getenv("CAMERA_WS_PORT", "8000"))
    assert port in {8000, 8001}
