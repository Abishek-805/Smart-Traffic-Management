"""Exercise the same QR -> registration -> start flow used by the mobile app."""
import argparse
import asyncio
import json

import requests
import websockets


async def verify(base_url: str, direction: str):
    response = requests.get(
        f"{base_url.rstrip('/')}/api/v1/qr/generate",
        params={"direction": direction}, timeout=5)
    response.raise_for_status()
    qr = response.json()["data"]["payload"]
    ws_url = f"{qr['protocol']}://{qr['server']}:{qr['port']}/ws/camera"
    async with websockets.connect(ws_url, open_timeout=5) as socket:
        await socket.send(json.dumps({
            "version": "1.0", "type": "REGISTER_CAMERA", "token": qr["token"],
            "payload": {"node_id": qr["session"], "session": qr["session"],
                        "camera_direction": qr["camera_direction"],
                        "device": {}, "capabilities": {}},
        }))
        ack = json.loads(await asyncio.wait_for(socket.recv(), timeout=5))
        if ack.get("type") != "REGISTRATION_ACK":
            raise RuntimeError(f"registration failed: {ack}")
        start = json.loads(await asyncio.wait_for(socket.recv(), timeout=5))
        if start.get("type") != "START_STREAM":
            raise RuntimeError(f"start command missing: {start}")
        issued = ack["payload"]["session_token"]
        await socket.send(json.dumps({"version": "1.0", "type": "DISCONNECT",
            "token": issued, "payload": {"node_id": qr["session"],
            "session_token": issued, "reason": "pairing verification"}}))
    print(json.dumps({"status": "PASS", "direction": direction,
                      "server": qr["server"], "port": qr["port"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--direction", choices=("north", "east", "south", "west"), default="north")
    args = parser.parse_args()
    asyncio.run(verify(args.url, args.direction))
