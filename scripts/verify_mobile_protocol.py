"""Validate the native app's authorization, controls, frame ACK, and reconnect contract."""
import argparse
import asyncio
import base64
import json
import time

import cv2
import numpy as np
import requests
import websockets


async def receive_type(socket, expected: str, timeout: float = 15) -> dict:
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            raise TimeoutError(f"Timed out waiting for {expected}")
        message = json.loads(await asyncio.wait_for(socket.recv(), timeout=remaining))
        if message.get("type") == expected:
            return message
        if message.get("type") == "ERROR":
            raise RuntimeError(f"Server rejected request: {message}")


def registration(qr: dict, token: str) -> dict:
    return {
        "protocol_version": "1.0",
        "type": "REGISTER_CAMERA",
        "token": token,
        "payload": {
            "node_id": qr["session"],
            "session": qr["session"],
            "camera_direction": qr["camera_direction"],
            "device": {},
            "capabilities": {},
        },
    }


async def verify(base_url: str, direction: str) -> None:
    response = requests.get(
        f"{base_url.rstrip('/')}/api/v1/qr/generate",
        params={"direction": direction},
        timeout=5,
    )
    response.raise_for_status()
    qr = response.json()["data"]["payload"]
    ws_url = f"{qr['protocol']}://{qr['server']}:{qr['port']}/ws/camera"

    async with websockets.connect(ws_url, open_timeout=5) as unauthorized:
        await unauthorized.send(json.dumps(registration(qr, "invalid-token")))
        rejected = json.loads(await asyncio.wait_for(unauthorized.recv(), timeout=5))
        if rejected.get("payload", {}).get("error_code") != "UNAUTHORIZED_PAIRING":
            raise RuntimeError(f"Invalid pairing token was not rejected: {rejected}")

    started_at = time.perf_counter()
    async with websockets.connect(ws_url, open_timeout=5) as socket:
        await socket.send(json.dumps(registration(qr, qr["token"])))
        ack = await receive_type(socket, "REGISTRATION_ACK", 5)
        await receive_type(socket, "START_STREAM", 5)
        session_token = ack["payload"]["session_token"]
        node_id = qr["session"]

        def control(message_type: str) -> dict:
            return {
                "protocol_version": "1.0",
                "type": message_type,
                "token": session_token,
                "timestamp": time.time(),
                "payload": {"node_id": node_id, "session_token": session_token},
            }

        await socket.send(json.dumps(control("STOP_STREAM")))
        await receive_type(socket, "STOP_STREAM", 5)
        await socket.send(json.dumps(control("START_STREAM")))
        await receive_type(socket, "START_STREAM", 5)

        image = np.zeros((360, 640, 3), dtype=np.uint8)
        cv2.rectangle(image, (180, 120), (420, 300), (255, 255, 255), -1)
        ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 65])
        if not ok:
            raise RuntimeError("Could not create validation JPEG")
        frame_data = base64.b64encode(encoded.tobytes()).decode("ascii")
        frame_rtts = []
        server_times = []
        for index in range(6):
            captured = int(time.time() * 1000)
            frame_id = f"{direction.upper()}-LIVE-{index + 1:06d}"
            frame_started = time.perf_counter()
            await socket.send(json.dumps({
                "protocol_version": "1.0",
                "type": "VIDEO_FRAME",
                "token": session_token,
                "timestamp": captured,
                "payload": {
                    "node_id": node_id,
                    "session_token": session_token,
                    "camera_direction": direction,
                    "direction": direction,
                    "frame_id": frame_id,
                    "frame_data": frame_data,
                    "capture_timestamp": captured,
                    "upload_timestamp": captured,
                },
            }))
            frame_ack = await receive_type(socket, "FRAME_ACK", 20)
            frame_rtts.append((time.perf_counter() - frame_started) * 1000)
            server_times.append(float(frame_ack.get("payload", {}).get("server_processing_ms") or 0))

    # The server keeps an authenticated session for the bounded heartbeat timeout.
    async with websockets.connect(ws_url, open_timeout=5) as reconnected:
        await reconnected.send(json.dumps(registration(qr, session_token)))
        reconnect_ack = await receive_type(reconnected, "REGISTRATION_ACK", 5)
        await receive_type(reconnected, "START_STREAM", 5)
        renewed_token = reconnect_ack["payload"]["session_token"]
        await reconnected.send(json.dumps({
            "protocol_version": "1.0",
            "type": "DISCONNECT",
            "token": renewed_token,
            "timestamp": time.time(),
            "payload": {
                "node_id": node_id,
                "session_token": renewed_token,
                "reason": "protocol verification complete",
            },
        }))

    result = {
        "status": "PASS",
        "direction": direction,
        "server": f"{qr['server']}:{qr['port']}",
        "full_validation_ms": round((time.perf_counter() - started_at) * 1000, 1),
        "warm_frame_rtt_avg_ms": round(sum(frame_rtts[1:]) / len(frame_rtts[1:]), 1),
        "warm_server_processing_avg_ms": round(sum(server_times[1:]) / len(server_times[1:]), 1),
        "cold_frame_rtt_ms": round(frame_rtts[0], 1),
        "reconnect": "PASS",
        "invalid_token_rejected": True,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--direction", choices=("north", "east", "south", "west"), default="east")
    args = parser.parse_args()
    asyncio.run(verify(args.url, args.direction))
