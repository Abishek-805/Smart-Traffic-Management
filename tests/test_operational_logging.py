"""Operational logging and failure-visibility regression tests."""

import logging
from logging.handlers import RotatingFileHandler

import pytest

from ai.utils.logger import get_logger
from core.application_context import ApplicationContext
from server.message_handler import log_frame_trace
from server.runtime import run_runtime_iteration


def test_frame_trace_messages_are_debug_not_info(caplog):
    with caplog.at_level(logging.DEBUG, logger="TrafficSystem.MessageHandler"):
        log_frame_trace("YOLO_START", frame_id="north-1", direction="north")

    record = next(record for record in caplog.records if "YOLO_START" in record.message)
    assert record.levelno == logging.DEBUG


def test_file_handlers_are_rotating_and_bounded():
    handlers = [
        handler for handler in get_logger().handlers
        if isinstance(handler, RotatingFileHandler)
    ]
    assert len(handlers) >= 2
    assert all(handler.maxBytes > 0 and handler.backupCount > 0 for handler in handlers)


@pytest.mark.asyncio
async def test_runtime_iteration_logs_exception_and_increments_counter(caplog):
    ctx = ApplicationContext()

    async def failing_publish(_snapshot):
        raise ValueError("test failure")

    with caplog.at_level(logging.DEBUG, logger="TrafficSystem.Runtime"):
        completed = await run_runtime_iteration(ctx, object(), publish=failing_publish)

    assert not completed
    assert ctx.frame_processing_errors == 1
    assert any(
        record.levelno == logging.ERROR
        and "Runtime ticker failed" in record.message
        and "ValueError" in record.message
        and "test failure" in record.message
        for record in caplog.records
    )


def test_unavailable_resource_metrics_are_not_fabricated(monkeypatch):
    import builtins

    ctx = ApplicationContext()
    real_import = builtins.__import__

    def fail_psutil(name, *args, **kwargs):
        if name == "psutil":
            raise ImportError("not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_psutil)
    health = ctx.get_health_dict()

    assert health["cpu_percent"] is None
    assert health["memory_used_gb"] is None
    assert health["memory_total_gb"] is None
    assert health["inference_latency_ms"] is None
