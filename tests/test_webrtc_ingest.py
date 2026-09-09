"""Real local WebRTC transport tests; photograph is not a detection benchmark."""
import asyncio
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import cv2
import numpy as np
from aiortc import RTCConfiguration, RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame

from server.connection_manager import ConnectionManager
from server.session_manager import SessionManager


class PhotographTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.image = cv2.resize(cv2.imread(str(Path(__file__).parent / 'fixtures' / 'ultralytics_bus.jpg')), (320, 426))

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        frame = VideoFrame.from_ndarray(self.image, format='bgr24')
        frame.pts, frame.time_base = pts, time_base
        return frame


class RecordingHandler:
    def __init__(self):
        self.session_manager = SessionManager(timeout_sec=120)
        self.connection_manager = ConnectionManager()
        self.ctx = SimpleNamespace(system_running=True)
        self.frames = []

    async def submit_decoded_frame(self, image, direction, node_id, token, websocket, frame_id, received_ms):
        self.frames.append((node_id, direction, image, websocket, time.monotonic(), frame_id))


class WebRTCIngestTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        asyncio.get_running_loop().set_debug(False)
        from server.webrtc_ingest import WebRTCIngest
        self.handler = RecordingHandler()
        self.context_patch = patch('server.webrtc_ingest.ApplicationContext.get_instance', return_value=self.handler.ctx)
        self.context_patch.start()
        self.addCleanup(self.context_patch.stop)
        self.ingest = WebRTCIngest(self.handler)
        self.clients = []
        self.address_patch = patch('aioice.ice.get_host_addresses', return_value=['127.0.0.1'])
        self.address_patch.start()
        self.addCleanup(self.address_patch.stop)

    async def asyncTearDown(self):
        if hasattr(self, 'ingest'):
            await self.ingest.shutdown()
        await asyncio.gather(*(pc.close() for pc in getattr(self, 'clients', [])))

    async def connect(self, node, direction):
        session = self.handler.session_manager.create_session(node, direction)
        session.streaming = True
        websocket = object()
        self.handler.connection_manager.active_connections[node] = websocket
        pc = RTCPeerConnection(RTCConfiguration(iceServers=[]))
        self.clients.append(pc)
        pc.addTrack(PhotographTrack())
        await pc.setLocalDescription(await pc.createOffer())
        answer = await self.ingest.offer(node, session.session_token, websocket, pc.localDescription.sdp)
        await pc.setRemoteDescription(RTCSessionDescription(**answer))
        return pc, websocket, session

    async def until(self, predicate, timeout=12):
        async with asyncio.timeout(timeout):
            while not predicate():
                await asyncio.sleep(.05)

    async def test_four_real_video_peers_and_replacement_keep_direction_and_ownership(self):
        directions = ('north', 'south', 'east', 'west')
        connected = await asyncio.gather(*(self.connect(d, d) for d in directions))
        await self.until(lambda: all(sum(f[0] == d for f in self.handler.frames) >= 3 for d in directions))
        reference = PhotographTrack().image
        for direction in directions:
            frames = [f for f in self.handler.frames if f[0] == direction]
            self.assertTrue(all(f[1] == direction for f in frames))
            self.assertEqual(frames[0][2].shape, (426, 320, 3))
            self.assertLess(np.mean(np.abs(frames[0][2].astype(float) - reference)), 16)
            self.assertTrue(all(b[4] - a[4] >= .23 for a, b in zip(frames, frames[1:])))
        old_pc, old_ws, _ = connected[0]
        await old_pc.close()
        _, new_ws, _ = await self.connect('north', 'north')
        await self.ingest.close('north', old_ws)
        await self.until(lambda: any(f[3] is new_ws for f in self.handler.frames))
        mark = len(self.handler.frames)
        await self.until(lambda: all(any(f[0] == d for f in self.handler.frames[mark:]) for d in directions))
        self.assertFalse(any(f[3] is old_ws for f in self.handler.frames[mark:]))

    async def test_expired_token_stops_a_live_peer_and_pause_suppresses_frames(self):
        _, _, session = await self.connect('north', 'north')
        await self.until(lambda: len(self.handler.frames) >= 2)
        session.streaming = False
        await asyncio.sleep(.4)
        mark = len(self.handler.frames)
        await asyncio.sleep(.4)
        self.assertEqual(len(self.handler.frames), mark)
        session.streaming = True
        self.handler.ctx.system_running = False
        await asyncio.sleep(.4)
        self.assertEqual(len(self.handler.frames), mark)
        self.handler.ctx.system_running = True
        await self.until(lambda: len(self.handler.frames) > mark)
        session.last_heartbeat = time.time() - 121
        await asyncio.sleep(.4)
        mark = len(self.handler.frames)
        await asyncio.sleep(.4)
        self.assertEqual(len(self.handler.frames), mark)

    async def test_invalid_offer_and_audio_do_not_leave_peer_connections(self):
        session = self.handler.session_manager.create_session('north', 'north')
        session.streaming = True
        ws = object()
        self.handler.connection_manager.active_connections['north'] = ws
        with self.assertRaises((ValueError, PermissionError)):
            await self.ingest.offer('north', 'invalid', ws, 'bogus')
        with self.assertRaises(ValueError):
            await self.ingest.offer('north', session.session_token, ws, 'bogus')
        pc = RTCPeerConnection(RTCConfiguration(iceServers=[]))
        self.clients.append(pc)
        pc.addTrack(PhotographTrack())
        pc.addTransceiver('audio', direction='sendonly')
        await pc.setLocalDescription(await pc.createOffer())
        with self.assertRaises(ValueError):
            await self.ingest.offer('north', session.session_token, ws, pc.localDescription.sdp)
        self.assertEqual(self.ingest.peers, {})


if __name__ == '__main__':
    unittest.main()
