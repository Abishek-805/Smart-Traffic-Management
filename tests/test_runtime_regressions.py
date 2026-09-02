import asyncio
import importlib.util
import socket
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import fakeredis.aioredis
import numpy as np
import psutil
import pytest
from fastapi.testclient import TestClient

from ai.detection.detection_types import Detection
from ai.tracking.byte_tracker import ByteTracker
from core.application_context import ApplicationContext
from server.message_handler import MessageHandler
from server.runtime import runtime_snapshot
from server.session_manager import SessionManager
from ai.state.count_stabilizer import CountStabilizer
from ai.analytics.analytics_exporter import LaneStatistics
from web.app import app
from web.services import node_service


def test_tracker_instances_do_not_rewind_existing_ids():
    north = ByteTracker()
    car = Detection('car', 2, .9, (10, 10, 70, 70))
    first = north.update([car])[0].track_id
    east = ByteTracker()
    east.update([car])
    another = Detection('car', 2, .9, (200, 200, 260, 260))
    north.update([car, another])
    tracks = north.update([car, another])
    assert len({d.track_id for d in tracks}) == 2
    assert tracks[0].track_id == first
    assert north.tracker is not east.tracker
    assert north.tracker.frame_id == 3
    assert east.tracker.frame_id == 1


def test_bytetrack_low_confidence_detection_recovers_existing_track():
    tracker = ByteTracker()
    strong = Detection('car', 2, .9, (10, 10, 70, 70))
    first = tracker.update([strong])
    assert len(first) == 1

    # Between the low and high thresholds: preserve an existing ID without
    # allowing this weak observation to create a new track by itself.
    weak = Detection('car', 2, .1, (11, 10, 71, 70))
    recovered = tracker.update([weak])
    assert len(recovered) == 1
    assert recovered[0].track_id == first[0].track_id


def test_expired_tokens_cannot_revive_sessions():
    sessions = SessionManager(timeout_sec=1)
    session = sessions.create_session('test', 'north')
    session.last_heartbeat -= 2
    assert not sessions.update_heartbeat('test', session.session_token)


def test_unexpected_socket_loss_preserves_short_reconnect_window():
    handler = MessageHandler()
    session = handler.session_manager.create_session('reconnect-node', 'south')
    handler.handle_connection_loss('reconnect-node')
    assert handler.session_manager.validate_session('reconnect-node', session.session_token)


@pytest.mark.asyncio
async def test_frame_requires_socket_ownership_and_direction():
    handler = MessageHandler()
    socket = AsyncMock()
    handler.session_manager.register_pairing_session(
        'north', 'regression', 'pair-token', time.time() + 60
    )
    ack = await handler.process_message({'type': 'REGISTER_CAMERA', 'payload': {
        'node_id': 'regression', 'camera_direction': 'north'}, 'token': 'pair-token'}, socket)
    packet = {'type': 'VIDEO_FRAME', 'payload': {'node_id': 'regression',
        'session_token': ack['payload']['session_token'], 'direction': 'north', 'frame_data': 'a'}}
    assert (await handler.process_message(packet, AsyncMock()))['payload']['error_code'] == 'UNAUTHORIZED_SESSION'
    packet['payload']['direction'] = 'south'
    assert (await handler.process_message(packet, socket))['payload']['error_code'] == 'DIRECTION_MISMATCH'
    await handler.shutdown()


@pytest.mark.asyncio
async def test_registration_requires_matching_one_time_qr_token():
    handler = MessageHandler()
    handler.session_manager.register_pairing_session(
        'east', 'CAM-EAST-VALID', 'pair-secret', time.time() + 60
    )
    rejected = await handler.process_message({
        'type': 'REGISTER_CAMERA', 'token': 'wrong-secret',
        'payload': {'node_id': 'CAM-EAST-VALID', 'camera_direction': 'east'},
    }, AsyncMock())
    assert rejected['payload']['error_code'] == 'UNAUTHORIZED_PAIRING'

    accepted = await handler.process_message({
        'type': 'REGISTER_CAMERA', 'token': 'pair-secret',
        'payload': {'node_id': 'CAM-EAST-VALID', 'camera_direction': 'east'},
    }, AsyncMock())
    assert accepted['type'] == 'REGISTRATION_ACK'
    assert handler.session_manager.get_pairing_session('east') is None
    await handler.shutdown()


def test_freshness_is_per_direction_and_idle_is_not_green():
    ctx = ApplicationContext()
    for direction in ('north', 'east'):
        ctx.session_manager.create_session(direction, direction)
    ctx.frame_updated_at = {'north': time.monotonic(), 'east': time.monotonic() - 10}
    payload = runtime_snapshot(ctx)['payload']
    assert payload['lanes']['north']['streamStatus'] == 'LIVE'
    assert payload['lanes']['east']['streamStatus'] == 'STALE'
    ctx.system_running = False
    payload = runtime_snapshot(ctx)['payload']
    assert payload['signalState'] == 'ALL_RED'
    assert not payload['pipelineHealthy']


def test_scheduler_diagnostics_buffer_is_bounded():
    stabilizer = CountStabilizer()
    for count in range(400):
        stabilizer.stabilize({'north': LaneStatistics('north', live_count=count)})
    assert len(stabilizer._report_entries) == 256


def test_telemetry_endpoint_accepts_and_reports_idle_state():
    with TestClient(app).websocket_connect('/ws/telemetry') as ws:
        packet = ws.receive_json()
        assert set(packet['payload']['lanes']) == {'north', 'south', 'east', 'west'}


def test_default_pairing_qr_targets_combined_runtime(monkeypatch):
    monkeypatch.delenv('CAMERA_WS_PORT', raising=False)
    with TestClient(app) as client:
        response = client.get('/api/v1/qr/generate?direction=east')
        assert response.status_code == 200
        pairing = response.json()['data']
        assert pairing['payload']['port'] == 8000
        assert pairing['payload']['camera_direction'] == 'east'
        assert pairing['qr_image'].startswith('data:image/png;base64,')


def test_pairing_qr_prefers_active_windows_hotspot_address(monkeypatch):
    """A phone joined to Mobile Hotspot must receive the hotspot gateway in its QR."""
    class RouteSocket:
        def connect(self, _address):
            pass

        def getsockname(self):
            return ('192.168.137.137', 50000)

        def close(self):
            pass

    monkeypatch.setattr(socket, 'socket', lambda *_args, **_kwargs: RouteSocket())
    monkeypatch.setattr(psutil, 'net_if_addrs', lambda: {
        'Wi-Fi': [SimpleNamespace(family=socket.AF_INET, address='192.168.137.137')],
        'Local Area Connection* 2': [
            SimpleNamespace(family=socket.AF_INET, address='192.168.137.1')
        ],
    })
    monkeypatch.setattr(psutil, 'net_if_stats', lambda: {
        'Wi-Fi': SimpleNamespace(isup=True),
        'Local Area Connection* 2': SimpleNamespace(isup=True),
    })

    assert node_service.get_local_ip() == '192.168.137.1'


def test_pairing_qr_falls_back_when_adapter_discovery_fails(monkeypatch):
    class RouteSocket:
        def connect(self, _address):
            pass

        def getsockname(self):
            return ('10.2.11.221', 50000)

        def close(self):
            pass

    monkeypatch.setattr(socket, 'socket', lambda *_args, **_kwargs: RouteSocket())
    monkeypatch.setattr(psutil, 'net_if_stats', lambda: (_ for _ in ()).throw(OSError('unavailable')))

    assert node_service.get_local_ip() == '10.2.11.221'


def test_legacy_api_redirect_cannot_repeat_v1_prefix():
    with TestClient(app, follow_redirects=False) as client:
        legacy = client.get('/api/system/health')
        assert legacy.status_code == 308
        assert legacy.headers['location'] == '/api/v1/system/health'
        unknown_canonical = client.get('/api/v1/does-not-exist')
        assert unknown_canonical.status_code == 404


def load_service(name, relative):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_split_redis_retained_snapshot_frame_and_ack(monkeypatch):
    rest_cls = load_service('rest_redis', 'app-backend/app/services/redis_service.py').AppBackendRedisService
    ws_cls = load_service('ws_redis', 'websocket-server/app/services/redis_broadcaster.py').WebSocketRedisBroadcaster
    rest, ws = rest_cls(), ws_cls()
    shared_server = fakeredis.FakeServer()
    rest.redis_client = fakeredis.aioredis.FakeRedis(server=shared_server, decode_responses=True)
    ws.redis_client = fakeredis.aioredis.FakeRedis(server=shared_server, decode_responses=True)
    rest.is_connected = ws.is_connected = True
    runtime_ctx = ApplicationContext()
    runtime_ctx.frame_buffer['north'] = b'jpeg-preview'
    monkeypatch.setattr(ApplicationContext, '_instance', runtime_ctx)
    await ws.publish_telemetry({'timestamp': time.time(), 'payload': {'systemRunning': True, 'nodes': [{'node_id': 'north'}],
        'lanes': {'north': {'streamStatus': 'LIVE', 'frameAgeMs': 20}}}})
    rest_ctx = ApplicationContext()
    monkeypatch.setattr(ApplicationContext, '_instance', rest_ctx)
    listener = asyncio.create_task(rest.start_listener())
    async def apply(command, payload):
        return {'status': 'SUCCESS', 'message': command}
    commands = asyncio.create_task(ws.start_listener(apply))
    try:
        for _ in range(20):
            if rest_ctx.latest_snapshot:
                break
            await asyncio.sleep(.05)
        assert rest_ctx.remote_nodes == [{'node_id': 'north'}]
        assert rest_ctx.frame_buffer['north'] == b'jpeg-preview'
        result = await rest.publish_command('STOP')
        assert result['message'] == 'STOP'
    finally:
        listener.cancel()
        commands.cancel()
        await asyncio.gather(listener, commands, return_exceptions=True)
        await rest.close()
        await ws.close()


@pytest.mark.asyncio
async def test_missing_redis_never_reports_command_success():
    cls = load_service('rest_no_redis', 'app-backend/app/services/redis_service.py').AppBackendRedisService
    with pytest.raises(RuntimeError, match='not applied'):
        await cls().publish_command('STOP')

@pytest.mark.asyncio
async def test_configuration_changes_runtime_and_rejects_invalid_bounds(monkeypatch):
    import threading
    from types import SimpleNamespace
    from server.runtime import handle_command
    ctx = ApplicationContext()
    ctx.pipeline = SimpleNamespace(_lock=threading.RLock(),
        model_manager=SimpleNamespace(confidence=.35),
        signal_scheduler=SimpleNamespace(min_green_sec=10, max_green_sec=60))
    monkeypatch.setattr(ApplicationContext, '_instance', ctx)
    await handle_command('CONFIGURE', {'confidenceThreshold': .6, 'minGreenTime': 15, 'maxGreenTime': 40})
    assert ctx.pipeline.model_manager.confidence == .6
    assert ctx.pipeline.signal_scheduler.min_green_sec == 15
    assert ctx.pipeline.signal_scheduler.max_green_sec == 40
    with pytest.raises(ValueError):
        await handle_command('CONFIGURE', {'confidenceThreshold': .6, 'minGreenTime': 50, 'maxGreenTime': 40})
    assert ctx.pipeline.signal_scheduler.min_green_sec == 15
    await handle_command('CONFIGURE', {'confidenceThreshold': .08, 'minGreenTime': 15, 'maxGreenTime': 40})
    assert ctx.pipeline.model_manager.confidence == .08
    client = TestClient(app)
    assert client.post('/api/v1/system/config', json={'confidenceThreshold': .5}).status_code == 422
