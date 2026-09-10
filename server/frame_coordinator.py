"""One bounded handoff for JPEG and decoded video; never queue executor work."""
import asyncio
import base64
import time
import logging

logger = logging.getLogger(__name__)


def process_batch(packets):
    import cv2
    import numpy as np
    from core.application_context import ApplicationContext
    from server.frame_normalization import normalize_frame_orientation
    from server.message_handler import _process_frame_locked, _frame_worker_lock
    from ai.pipeline.traffic_pipeline import detector_is_due
    from config.model import DETECTOR_FPS
    ctx = ApplicationContext.get_instance()
    ready = []
    with _frame_worker_lock:
        for packet in packets:
            p = packet['payload']
            if not ctx.system_running or time.time()*1000 - packet['backend_receive_timestamp'] > 2500:
                ctx.increment_stage_counter('dropped')
                continue
            try:
                image = p.get('decoded_image')
                if image is None:
                    data = p['frame_data']
                    raw = data if isinstance(data, bytes) else base64.b64decode(data.split(',')[-1], validate=True)
                    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
                if image is None:
                    raise ValueError('Invalid JPEG')
                image, orientation = normalize_frame_orientation(image, p.get('rotation', 0))
                ready.append((packet, image, orientation, time.time() * 1000))
            except (ValueError, TypeError, cv2.error):
                ctx.increment_stage_counter('decode_failed')
        if not ready:
            return []
        if ctx.pipeline is None:
            from ai.pipeline.traffic_pipeline import TrafficPipeline
            ctx.pipeline = TrafficPipeline(save_output=False, headless=True)
        due = [(packet, image) for packet, image, _, _ in ready
               if detector_is_due(ctx.pipeline._last_detection_ts.get(packet['payload']['direction']),
                                  packet['payload']['capture_timestamp']/1000, DETECTOR_FPS)]
        computed = {}
        # Warm-up and inference share the model manager's validated batch size.
        size = ctx.pipeline.model_manager.batch_size
        for start in range(0, len(due), size):
            group = due[start:start+size]
            boxes, elapsed = ctx.pipeline.detector.detect_batch(
                [image for _, image in group],
                [getattr(ctx.pipeline, '_frame_count', 0)+i+1 for i in range(len(group))],
                [packet['payload']['capture_timestamp']/1000 for packet, _ in group])
            for (packet, _), detections in zip(group, boxes):
                computed[packet['payload']['direction']] = (detections, elapsed)
        results = []
        for packet, image, orientation, preprocess_done_ms in ready:
            p = packet['payload']
            result = _process_frame_locked('', p['direction'], p['capture_timestamp'],
                p.get('upload_timestamp',p['capture_timestamp']), packet['backend_receive_timestamp'],
                p['frame_id'], 0, decoded=(image,orientation),
                precomputed_detection=computed.get(p['direction']))
            if result:
                result[3]['queue_wait_ms'] = round(max(0, preprocess_done_ms - packet['backend_receive_timestamp']), 2)
                result[3]['batch_size'] = min(size, len(due))
                result[3]['source_kind'] = p.get('source_kind','jpeg')
                results.append((packet,result))
        return results


async def run_coordinator(handler):
    from core.application_context import ApplicationContext
    ctx = ApplicationContext.get_instance()
    while True:
        await handler.batch_ready.wait()
        await asyncio.sleep(.02)
        packets = list(handler.latest_frames.values())
        handler.latest_frames.clear()
        handler.batch_ready.clear()
        try:
            results = await asyncio.get_running_loop().run_in_executor(handler.frame_executor, process_batch, packets)
            for packet, result in results:
                p = packet['payload']
                node = p.get('node_id')
                if (not ctx.system_running or not handler.session_manager.validate_session(node,p.get('session_token'))
                    or handler.connection_manager.get_connection(node) is not packet.get('owner_socket')):
                    ctx.increment_stage_counter('dropped')
                    continue
                direction, jpeg, snapshot, telemetry = result
                previous = ctx.frame_updated_at.get(direction)
                telemetry['fps'] = round(1/max(.001,time.monotonic()-previous),1) if previous else 0
                ctx.frame_buffer[direction] = jpeg
                ctx.frame_buffer['active'] = jpeg
                ctx.frame_updated_at[direction] = time.monotonic()
                ctx.live_telemetry[direction] = telemetry
                ctx.last_frame_monotonic = time.monotonic()
                ctx.last_telemetry_frame_id = p['frame_id']
                ctx.increment_stage_counter('processed')
                await ctx.update_snapshot(snapshot)
                await handler.connection_manager.send_to_node(node, {'type':'FRAME_ACK','payload':{
                    'frame_id':p['frame_id'],'direction':direction,
                    'server_processing_ms':telemetry['server_processing_ms'],
                    'queue_wait_ms':telemetry['queue_wait_ms'],
                    'inference_ms':telemetry['yolo_latency_ms'],
                    'vehicle_count':snapshot['payload']['lanes'][direction]['vehicles']}})
        except asyncio.CancelledError:
            raise
        except Exception:
            ctx.frame_processing_errors += 1
            logger.exception('Camera batch failed')
