"""Four QR-authenticated WebRTC streams through the real YOLO runtime.

Uses different real photographs as encoded video. Counts are execution checks,
not labelled accuracy. --seconds controls duration; no generated traffic images.
"""
import asyncio
import json
import time
from pathlib import Path
from contextlib import AsyncExitStack
from fractions import Fraction
import cv2
import httpx
import websockets
from aiortc import RTCPeerConnection, RTCConfiguration, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame

ROOT=Path(__file__).resolve().parents[1]

class RoadTrack(VideoStreamTrack):
    def __init__(self,path):
        super().__init__()
        image=cv2.imread(str(path))
        if image is None: raise ValueError(path)
        h,w=image.shape[:2]
        self.image=cv2.resize(image,(round(w*640/max(w,h)),round(h*640/max(w,h))))
        self.index=0
    async def recv(self):
        await asyncio.sleep(.1)
        frame=VideoFrame.from_ndarray(self.image,format='bgr24')
        frame.pts=self.index*9000;frame.time_base=Fraction(1,90000);self.index+=1
        return frame

async def run(seconds=20):
    paths=['outputs/diagnostics/traffic_source_crop.jpg','tests/fixtures/ultralytics_bus.jpg',
           'outputs/diagnostics/traffic_mobile_1280_q75.jpg','outputs/diagnostics/traffic_mobile_640_q65.jpg']
    peers=[];tasks=[];results={d:[] for d in ('north','east','south','west')}
    async with AsyncExitStack() as stack:
        client=await stack.enter_async_context(httpx.AsyncClient(base_url='http://127.0.0.1:8000',timeout=15))
        nodes=(await client.get('/api/v1/mobile-nodes')).json()['data']
        if nodes['summary']['connected_nodes']: raise RuntimeError('Disconnect cameras before test')
        await client.post('/api/v1/system/start')
        async def connect(direction,path):
            qr=(await client.get('/api/v1/qr/generate',params={'direction':direction})).json()['data']['payload']
            ws=await stack.enter_async_context(websockets.connect('ws://127.0.0.1:8000/ws/camera'))
            await ws.send(json.dumps({'type':'REGISTER_CAMERA','token':qr['token'],'payload':{'node_id':qr['session'],'camera_direction':direction}}))
            ack=json.loads(await ws.recv());assert ack['type']=='REGISTRATION_ACK',ack
            token=ack['payload']['session_token'];node=qr['session']
            async def heartbeats():
                while True:
                    await ws.send(json.dumps({'type':'HEARTBEAT','token':token,'payload':{'node_id':node}}))
                    await asyncio.sleep(2)
            tasks.append(asyncio.create_task(heartbeats()))
            pc=RTCPeerConnection(RTCConfiguration(iceServers=[]));peers.append(pc)
            pc.addTrack(RoadTrack(ROOT/path))
            await pc.setLocalDescription(await pc.createOffer())
            await ws.send(json.dumps({'type':'WEBRTC_OFFER','token':token,'payload':{'node_id':node,'sdp':pc.localDescription.sdp}}))
            async with asyncio.timeout(15):
                while True:
                    packet=json.loads(await ws.recv())
                    if packet['type']=='ERROR': raise RuntimeError(packet)
                    if packet['type']=='WEBRTC_ANSWER':
                        await pc.setRemoteDescription(RTCSessionDescription(**packet['payload']));break
            async def receive():
                async for raw in ws:
                    packet=json.loads(raw)
                    if packet['type']=='FRAME_ACK':
                        assert packet['payload']['direction']==direction
                        results[direction].append(packet['payload'])
            tasks.append(asyncio.create_task(receive()))
        try:
            await asyncio.gather(*(connect(d,p) for d,p in zip(results,paths)))
            await asyncio.sleep(seconds)
            import numpy as np
            report={'scope':'Four real WebRTC video peers replaying separate photographs through QR, YOLO and ByteTrack; not physical-phone or moving-video accuracy.',
                    'seconds':seconds,'lanes':{d:{'processed':len(rows),
                    'server_p95_ms':round(float(np.percentile([r['server_processing_ms'] for r in rows],95)),2) if rows else None,
                    'last_count':rows[-1]['vehicle_count'] if rows else None} for d,rows in results.items()}}
            (ROOT/'docs/benchmarks/four-webrtc-runtime.json').write_text(json.dumps(report,indent=2))
            print(json.dumps(report,indent=2))
            assert all(len(rows)>=3 and any(r['vehicle_count']>0 for r in rows) for rows in results.values()),'Every lane must detect real vehicles'
        finally:
            for task in tasks: task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
            await asyncio.gather(*(pc.close() for pc in peers))

if __name__=='__main__':
    asyncio.run(run())
