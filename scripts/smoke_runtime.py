"""Exercise four simulated camera clients against an already running local runtime.

Uses synthetic blank JPEGs to test transport and isolation, not detector accuracy.
Run: .venv/Scripts/python scripts/smoke_runtime.py
"""
import asyncio
import base64
import json
import time
from contextlib import AsyncExitStack

import cv2
import httpx
import numpy as np
import websockets


async def main():
    directions = ('north', 'east', 'south', 'west')
    _, image = cv2.imencode('.jpg', np.zeros((360, 640, 3), np.uint8))
    jpeg = base64.b64encode(image).decode()
    async with AsyncExitStack() as stack:
        http = await stack.enter_async_context(httpx.AsyncClient(base_url='http://127.0.0.1:8000'))
        await http.post('/api/v1/system/start')
        clients = []
        for direction in directions:
            ws = await stack.enter_async_context(websockets.connect('ws://127.0.0.1:8000/ws/camera'))
            node = 'SMOKE-' + direction.upper()
            await ws.send(json.dumps({'type': 'REGISTER_CAMERA', 'payload': {'node_id': node, 'camera_direction': direction}}))
            ack = json.loads(await asyncio.wait_for(ws.recv(), 5))
            assert ack['type'] == 'REGISTRATION_ACK', ack
            clients.append((ws, node, ack['payload']['session_token'], direction))

        async def send_frame(client):
            ws, node, token, direction = client
            await ws.send(json.dumps({'type': 'VIDEO_FRAME', 'token': token, 'payload': {
                'node_id': node, 'direction': direction, 'frame_data': jpeg,
                'frame_id': f'{direction}-{time.time_ns()}', 'capture_timestamp': time.time() * 1000}}))

        for _ in range(6):
            await asyncio.gather(*(send_frame(c) for c in clients))
            await asyncio.sleep(.5)
        telemetry = await stack.enter_async_context(websockets.connect('ws://127.0.0.1:8000/ws/telemetry'))
        first = json.loads(await telemetry.recv())['payload']
        assert all(first['lanes'][d]['streamStatus'] == 'LIVE' for d in directions), first
        nodes = (await http.get('/api/v1/mobile-nodes')).json()['data']
        assert nodes['summary']['connected_nodes'] == 4, nodes
        # Keep north running while the other cameras stop sending frames.
        for _ in range(8):
            await send_frame(clients[0])
            await asyncio.sleep(.5)
        for _ in range(10):
            latest = json.loads(await telemetry.recv())['payload']
            if latest['lanes']['east']['streamStatus'] == 'STALE':
                break
        assert latest['lanes']['north']['streamStatus'] == 'LIVE'
        assert latest['lanes']['east']['streamStatus'] == 'STALE'
        stop = await http.post('/api/v1/system/stop')
        assert stop.json()['data']['status'] == 'SUCCESS'
        status = (await http.get('/api/v1/system/status')).json()['data']
        assert status['running'] is False
        await http.post('/api/v1/system/start')
        print('PASS: four directions registered and processed; independent staleness; REST stop/start acknowledged.')


if __name__ == '__main__':
    asyncio.run(main())
