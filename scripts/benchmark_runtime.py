"""Reproducible four-camera transport/load benchmark, using explicit local test clips.
Never starts demo inputs in the application. Run with no physical cameras connected.
"""
import argparse, asyncio, base64, json, time
from pathlib import Path
from contextlib import AsyncExitStack, suppress
import cv2, numpy as np, psutil, websockets, httpx

def summarize(values):
    return {k:round(float(np.percentile(values,p)),2) for k,p in [('p50',50),('p95',95),('p99',99)]} if values else None

async def benchmark(args):
    directions=('north','east','south','west')
    frames={}
    for direction in directions:
        cap=cv2.VideoCapture(str(Path(args.videos)/f'{direction}.mp4'))
        if not cap.isOpened(): raise RuntimeError(f'Missing explicit test clip: {direction}')
        bank=[]
        native_fps=cap.get(cv2.CAP_PROP_FPS) or 30
        for i in range(32):
            cap.set(cv2.CAP_PROP_POS_MSEC, i * 1000/args.fps)
            ok,frame=cap.read()
            if not ok: break
            h,w=frame.shape[:2]; scale=min(1,args.edge/max(h,w))
            frame=cv2.resize(frame,(round(w*scale),round(h*scale)))
            _,jpeg=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,65])
            bank.append(base64.b64encode(jpeg).decode())
        cap.release()
        if not bank: raise RuntimeError(f'Empty test clip: {direction}')
        frames[direction]=bank
    results={d:{'ack_ms':[],'server_ms':[],'queue_ms':[],'inference_ms':[],
        'preview_ms':[],'counts':[],'sent':0,'bytes':0,'acked':0} for d in directions}
    pending={}; tasks=[]; samples=[]
    proc=psutil.Process(args.pid)
    async with AsyncExitStack() as stack:
        http=await stack.enter_async_context(httpx.AsyncClient(base_url=args.url,timeout=10))
        nodes=(await http.get('/api/v1/mobile-nodes')).json()['data']
        if nodes['summary']['connected_nodes']: raise RuntimeError('Disconnect real cameras before benchmarking.')
        await http.post('/api/v1/system/start')
        wsbase=args.url.replace('http','ws',1)
        clients=[]
        for d in directions:
            qr=(await http.get('/api/v1/qr/generate',params={'direction':d})).json()['data']['payload']
            ws=await stack.enter_async_context(websockets.connect(wsbase+'/ws/camera',max_size=4*1024*1024))
            node=qr['session']
            await ws.send(json.dumps({'type':'REGISTER_CAMERA','token':qr['token'],
                'payload':{'node_id':node,'session':node,'camera_direction':d}}))
            ack=json.loads(await ws.recv())
            if ack['type']!='REGISTRATION_ACK': raise RuntimeError(str(ack))
            clients.append((d,ws,node,ack['payload']['session_token']))
        started=time.perf_counter(); warmup=5; measured_start=started+warmup; finish=measured_start+args.seconds
        async def receive(d,ws):
            async for raw in ws:
                packet=json.loads(raw)
                if packet['type']!='FRAME_ACK': continue
                p=packet['payload']; key=p['frame_id']; item=pending.get(key)
                if not item or item < measured_start: continue
                r=results[d]; r['acked']+=1
                r['ack_ms'].append((time.perf_counter()-item)*1000)
                for out,field in [('server_ms','server_processing_ms'),('queue_ms','queue_wait_ms'),('inference_ms','inference_ms')]:
                    r[out].append(p[field])
                r['counts'].append(p['vehicle_count'])
        async def send(d,ws,node,token):
            index=0
            while time.perf_counter()<finish:
                deadline=started+index/args.fps
                await asyncio.sleep(max(0,deadline-time.perf_counter()))
                frame=frames[d][index%len(frames[d])]; key=f'{d}-{index}'; now=time.perf_counter()
                pending[key]=now
                packet={'type':'VIDEO_FRAME','token':token,'payload':{'node_id':node,'direction':d,
                    'frame_id':key,'frame_data':frame,'capture_timestamp':time.time()*1000}}
                encoded=json.dumps(packet); await ws.send(encoded)
                if index % max(1, int(args.fps * 2)) == 0:
                    await ws.send(json.dumps({'type':'HEARTBEAT','token':token,
                        'payload':{'node_id':node,'session_token':token,'client_timestamp':time.time()*1000}}))
                if now>=measured_start: results[d]['sent']+=1; results[d]['bytes']+=len(encoded)
                index+=1
        async def resources():
            proc.cpu_percent()
            while time.perf_counter()<finish:
                if time.perf_counter()>=measured_start:
                    samples.append((proc.cpu_percent(),proc.memory_info().rss/1024**2,proc.num_threads()))
                await asyncio.sleep(.5)
        async def preview(d):
            while time.perf_counter()<finish:
                try:
                    async with http.stream('GET',f'/api/v1/cameras/{d}/feed') as response:
                        buffer=b''
                        async for part in response.aiter_bytes():
                            buffer+=part
                            while b'\r\n\r\n' in buffer:
                                header,body=buffer.split(b'\r\n\r\n',1)
                                length=next((int(l.split(b':')[1]) for l in header.split(b'\r\n') if l.startswith(b'Content-Length:')),None)
                                if length is None:
                                    buffer=body[-300000:]; break
                                if len(body)<length: break
                                key=next((l.split(b':',1)[1].strip().decode() for l in header.split(b'\r\n') if l.startswith(b'X-Frame-Id:')),None)
                                sent=pending.get(key,0)
                                if sent>=measured_start: results[d]['preview_ms'].append((time.perf_counter()-sent)*1000)
                                buffer=body[length+2:]
                except (httpx.HTTPError,ValueError): pass
                await asyncio.sleep(.1)
        for d,ws,node,token in clients:
            tasks.extend([asyncio.create_task(receive(d,ws)),asyncio.create_task(send(d,ws,node,token)),asyncio.create_task(preview(d))])
        tasks.append(asyncio.create_task(resources()))
        try:
            await asyncio.sleep(warmup+args.seconds+1)
        finally:
            for t in tasks:t.cancel()
            outcomes = await asyncio.gather(*tasks,return_exceptions=True)
            errors = [str(e) for e in outcomes if isinstance(e, Exception)]
            if errors: raise RuntimeError('Benchmark task failure: ' + '; '.join(errors))
    out={'config':{'fps_per_camera':args.fps,'edge':args.edge,'seconds':args.seconds,'warmup':warmup},
        'scope':'Four localhost WebSocket clients replaying local clips; ACK and preview arrival, not physical phone latency or accuracy.',
        'directions':{},'resources':{'cpu_percent_one_core_100':summarize([s[0] for s in samples]),
            'rss_mb':summarize([s[1] for s in samples]),'rss_growth_mb':round(samples[-1][1]-samples[0][1],2) if samples else None}}
    for d,r in results.items():
        if r['sent'] < args.fps * args.seconds * .9:
            raise RuntimeError(f'{d}: insufficient offered load; benchmark invalid')
        out['directions'][d]={k:summarize(r[k]) for k in ['ack_ms','server_ms','queue_ms','inference_ms','preview_ms']}
        out['directions'][d].update(sent=r['sent'],acked=r['acked'],ack_fps=round(r['acked']/args.seconds,2),
            upload_kbps=round(r['bytes']*8/1000/args.seconds,1),count_range=[min(r['counts']),max(r['counts'])] if r['counts'] else [])
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8000');p.add_argument('--pid',type=int,required=True)
    p.add_argument('--videos',required=True);p.add_argument('--seconds',type=int,default=20);p.add_argument('--fps',type=float,default=4)
    p.add_argument('--edge',type=int,default=640);p.add_argument('--output',required=True)
    asyncio.run(benchmark(p.parse_args()))
