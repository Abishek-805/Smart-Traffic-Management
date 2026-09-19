import asyncio
import time
from unittest.mock import patch
import pytest
from server.message_handler import MessageHandler
from core.application_context import ApplicationContext

@pytest.mark.asyncio
async def test_newest_four_slots_are_selected_after_worker_is_available():
    from server.frame_coordinator import run_coordinator
    from server.frame_slots import LatestFrameSlots
    handler = MessageHandler()
    handler.frame_slots = LatestFrameSlots(('north', 'east', 'south', 'west'))
    handler.batch_ready = asyncio.Event()
    handler.worker_tasks = {}
    ctx = ApplicationContext.get_instance()
    ctx.system_running = True
    seen = []
    def process(packets, slots=None):
        seen.append([p['payload']['frame_id'] for p in packets])
        time.sleep(.08)
        return []
    def put(n):
        for lane in ('north','east','south','west'):
            handler.frame_slots.offer(lane, {
                'backend_receive_timestamp':time.time()*1000,
                'backend_receive_monotonic':time.monotonic(),
                'payload':{'direction':lane,'frame_id':f'{lane}-{n}'}})
        handler.batch_ready.set()
    with patch('server.frame_coordinator.process_batch', side_effect=process):
        task = asyncio.create_task(run_coordinator(handler))
        put(1)
        await asyncio.sleep(.06)
        put(2)
        put(3)
        await asyncio.sleep(.25)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
    handler.frame_executor.shutdown()
    assert len(seen) == 2
    assert all(x.endswith('-3') for x in seen[1])
    assert len(seen[1]) == 4
