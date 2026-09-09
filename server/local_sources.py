"""Optional local capture into the same bounded inference slots as mobile video.

TRAFFIC_SOURCES_JSON='{"north":0,"east":"rtsp://camera/stream","south":"picamera:0"}'
Configuration is operator-owned; no unauthenticated URL-fetch endpoint is exposed.
"""
import asyncio
import json
import os
import threading
import time
import logging

logger = logging.getLogger(__name__)

class LocalCameraSources:
    def __init__(self, handler):
        self.handler = handler
        self.stop = threading.Event()
        self.latest = {}
        self.lock = threading.Lock()
        self.threads = []
        self.nodes = {}
        self.task = None

    async def send_json(self, packet):
        pass  # Local capture has no network peer; telemetry remains in the dashboard.

    async def close(self, **kwargs):
        pass

    def _capture(self, direction, source):
        import cv2
        while not self.stop.is_set():
            camera = None
            pi = isinstance(source,str) and source.startswith('picamera:')
            try:
                if pi:
                    from picamera2 import Picamera2
                    camera = Picamera2(int(source.split(':')[1]))
                    camera.configure(camera.create_video_configuration(main={'size':(1280,720),'format':'RGB888'}))
                    camera.start()
                else:
                    if isinstance(source,str):
                        camera = cv2.VideoCapture(source,cv2.CAP_FFMPEG,[cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,3000,cv2.CAP_PROP_READ_TIMEOUT_MSEC,3000])
                    else:
                        camera = cv2.VideoCapture(source)
                    if not camera.isOpened(): raise RuntimeError('Camera unavailable')
                    camera.set(cv2.CAP_PROP_BUFFERSIZE,1)
                while not self.stop.is_set():
                    if pi: image = camera.capture_array('main')
                    else:
                        ok,image = camera.read()
                        if not ok: break
                    with self.lock:
                        self.latest[direction] = (image,time.time()*1000)
            except Exception:
                logger.exception('Local source %s failed; reconnecting',direction)
            finally:
                if camera is not None:
                    if pi: camera.close()
                    else: camera.release()
            self.stop.wait(2)

    async def start(self):
        sources = json.loads(os.getenv('TRAFFIC_SOURCES_JSON','{}'))
        if not isinstance(sources,dict) or set(sources)-{'north','east','south','west'}:
            raise ValueError('Camera sources must map north/east/south/west to source')
        for direction,source in sources.items():
            if isinstance(source,bool) or not isinstance(source,(str,int)):
                raise ValueError('Source must be USB index, file/RTSP URL or picamera:N')
            if self.handler.session_manager.get_session_by_direction(direction):
                raise ValueError(f'{direction} already has a camera')
            node=f'LOCAL-{direction}'
            session=self.handler.session_manager.create_session(node,direction)
            session.streaming=True
            self.nodes[direction]=(node,session.session_token)
            self.handler.connection_manager.active_connections[node]=self
            thread=threading.Thread(target=self._capture,args=(direction,source),daemon=True)
            self.threads.append(thread)
            thread.start()
        if sources: self.task=asyncio.create_task(self._pump())

    async def _pump(self):
        while True:
            for node,token in self.nodes.values(): self.handler.session_manager.update_heartbeat(node,token)
            with self.lock:
                frames,self.latest=self.latest,{}
            for direction,(image,received) in frames.items():
                node,token=self.nodes[direction]
                await self.handler.submit_decoded_frame(image,direction,node,token,self,time.time_ns(),received)
            await asyncio.sleep(.25)

    async def shutdown(self):
        self.stop.set()
        if self.task:
            self.task.cancel()
            await asyncio.gather(self.task,return_exceptions=True)
        for thread in self.threads: await asyncio.to_thread(thread.join,3.5)
        for node,_ in self.nodes.values():
            self.handler.session_manager.remove_session(node)
            self.handler.connection_manager.active_connections.pop(node,None)
