"""Compare CPU threading at identical weights, input size and thresholds."""
import os
os.environ.setdefault('OMP_WAIT_POLICY','PASSIVE')
os.environ.setdefault('KMP_BLOCKTIME','0')
import json, time
from pathlib import Path
import cv2, numpy as np, psutil, torch
from ultralytics import YOLO
model=YOLO('yolo26n.pt')
frame=cv2.imread('.venv/Lib/site-packages/ultralytics/assets/bus.jpg')
model.predict(frame,device='cpu',imgsz=640,conf=.35,classes=[2,3,5,7],verbose=False)
rows=[]; reference=None; proc=psutil.Process()
for threads in [8,4,2,1]:
    torch.set_num_threads(threads)
    for _ in range(4): model.predict(frame,device='cpu',imgsz=640,conf=.35,classes=[2,3,5,7],verbose=False)
    times=[]; t0=time.perf_counter(); c0=sum(proc.cpu_times()[:2])
    for _ in range(30):
        t=time.perf_counter();r=model.predict(frame,device='cpu',imgsz=640,conf=.35,classes=[2,3,5,7],verbose=False)
        times.append((time.perf_counter()-t)*1000)
    boxes=r[0].boxes.data.cpu().numpy()
    if reference is None: reference=boxes
    rows.append({'threads':threads,'p50_ms':round(float(np.median(times)),2),'p95_ms':round(float(np.percentile(times,95)),2),
        'cpu_seconds_per_frame':round((sum(proc.cpu_times()[:2])-c0)/30,4),
        'same_reference_boxes':bool(boxes.shape==reference.shape and np.allclose(boxes,reference,atol=.001)),
        'detections':len(boxes),'rss_mb':round(proc.memory_info().rss/1024**2,1)})
out={'scope':'Same pretrained bus image, not a model accuracy evaluation. CPU threading only, FP32 at 640.', 'results':rows}
Path('docs/benchmarks/inference-threads.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
