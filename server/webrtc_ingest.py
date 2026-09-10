"""Authenticated LAN WebRTC receivers with a bounded latest-frame handoff."""
import asyncio
import logging
import time
from dataclasses import dataclass, field

from aiortc import RTCConfiguration, RTCPeerConnection, RTCSessionDescription
from aiortc.mediastreams import MediaStreamError
from aiortc.sdp import SessionDescription

from core.application_context import ApplicationContext

logger = logging.getLogger(__name__)


@dataclass
class _Peer:
    pc: RTCPeerConnection
    node_id: str
    token: str
    websocket: object
    tasks: set = field(default_factory=set)
    latest: object = None
    ready: asyncio.Event = field(default_factory=asyncio.Event)
    frame_id: int = 0


class WebRTCIngest:
    """Own one peer per registered node; signaling is full SDP, without STUN."""

    def __init__(self, handler):
        self.handler = handler
        self.peers = {}
        self._cleanup_tasks = set()
        self._closed = False

    def _session(self, peer):
        if (self.peers.get(peer.node_id) is not peer
                or not self.handler.session_manager.validate_session(peer.node_id, peer.token)
                or self.handler.connection_manager.get_connection(peer.node_id) is not peer.websocket):
            return None
        return self.handler.session_manager.get_session(peer.node_id)

    def _streaming(self, peer):
        session = self._session(peer)
        return session if (session and getattr(session, 'streaming', False)
                           and ApplicationContext.get_instance().system_running) else None

    def _schedule_close(self, peer):
        task = asyncio.create_task(self._close_peer(peer))
        self._cleanup_tasks.add(task)
        task.add_done_callback(self._cleanup_done)

    def _cleanup_done(self, task):
        self._cleanup_tasks.discard(task)
        if not task.cancelled() and task.exception():
            logger.error('WebRTC cleanup failed', exc_info=task.exception())

    async def offer(self, node_id, token, websocket, sdp):
        if self._closed:
            raise ValueError('WebRTC ingest is shut down')
        if (not self.handler.session_manager.validate_session(node_id, token)
                or self.handler.connection_manager.get_connection(node_id) is not websocket):
            raise PermissionError('Invalid camera session')
        if not isinstance(sdp, str) or len(sdp) > 100_000:
            raise ValueError('Invalid SDP offer')
        try:
            description = SessionDescription.parse(sdp)
        except Exception as exc:
            raise ValueError('Invalid SDP offer') from exc
        if (len(description.media) != 1 or description.media[0].kind != 'video'
                or description.media[0].direction not in ('sendonly', 'sendrecv')):
            raise ValueError('Offer must send exactly one video track and no audio or data')
        peer = _Peer(RTCPeerConnection(RTCConfiguration(iceServers=[])), node_id, token, websocket)
        old = self.peers.get(node_id)
        self.peers[node_id] = peer

        @peer.pc.on('track')
        def on_track(track):
            logger.info('WebRTC track received node=%s kind=%s', node_id, track.kind)
            if track.kind != 'video' or peer.tasks:
                self._schedule_close(peer)
                return
            peer.tasks.add(asyncio.create_task(self._receive(peer, track)))
            peer.tasks.add(asyncio.create_task(self._sample(peer)))

        @peer.pc.on('connectionstatechange')
        def on_state_change():
            logger.info('WebRTC state node=%s state=%s', node_id, peer.pc.connectionState)
            if peer.pc.connectionState in ('failed', 'closed') and self.peers.get(node_id) is peer:
                self._schedule_close(peer)

        try:
            async with asyncio.timeout(10):
                if old:
                    await self._close_peer(old)
                await peer.pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type='offer'))
                await peer.pc.setLocalDescription(await peer.pc.createAnswer())
                if not self._session(peer):
                    raise PermissionError('Camera session changed during negotiation')
                return {'sdp': peer.pc.localDescription.sdp, 'type': 'answer'}
        except BaseException:
            await self._close_peer(peer)
            raise

    async def _receive(self, peer, track):
        try:
            while True:
                frame = await track.recv()
                # Validate every received frame, including frames dropped by sampling.
                if not self._session(peer):
                    break
                if not self._streaming(peer):
                    peer.latest = None
                    continue
                peer.frame_id += 1
                peer.latest = (frame, peer.frame_id, time.time() * 1000)
                peer.ready.set()
        except (MediaStreamError, asyncio.CancelledError):
            pass
        except Exception:
            logger.exception('WebRTC receive failed for %s', peer.node_id)
        finally:
            if self.peers.get(peer.node_id) is peer:
                self._schedule_close(peer)

    async def _sample(self, peer):
        next_sample = 0.0
        try:
            while True:
                await peer.ready.wait()
                await asyncio.sleep(max(0, next_sample - time.monotonic()))
                latest, peer.latest = peer.latest, None
                peer.ready.clear()
                session = self._streaming(peer)
                if latest is None or session is None:
                    continue
                frame, frame_id, received_ms = latest
                next_sample = time.monotonic() + .25
                # aiortc does not negotiate RTP video-orientation. The sender
                # must encode upright pixels; never apply phone metadata twice.
                image = await asyncio.to_thread(frame.to_ndarray, format='bgr24')
                session = self._streaming(peer)
                if session:
                    await self.handler.submit_decoded_frame(
                        image, session.camera_direction, peer.node_id, peer.token,
                        peer.websocket, frame_id, received_ms)
                    next_sample = time.monotonic() + .25
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception('WebRTC frame submission failed for %s', peer.node_id)
            self._schedule_close(peer)

    async def _close_peer(self, peer):
        if self.peers.get(peer.node_id) is peer:
            self.peers.pop(peer.node_id)
        tasks = [task for task in peer.tasks if task is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        peer.tasks.clear()
        peer.latest = None
        await peer.pc.close()

    async def close(self, node_id, websocket=None):
        peer = self.peers.get(node_id)
        if peer and (websocket is None or peer.websocket is websocket):
            await self._close_peer(peer)

    async def shutdown(self):
        self._closed = True
        await asyncio.gather(*(self._close_peer(peer) for peer in list(self.peers.values())))
        if self._cleanup_tasks:
            await asyncio.gather(*list(self._cleanup_tasks), return_exceptions=True)
