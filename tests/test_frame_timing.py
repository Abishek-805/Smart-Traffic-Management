import math

import pytest

from server.frame_timing import FrameTiming


def test_stage_durations_use_monotonic_clock():
    timing = FrameTiming(received_monotonic=10.0)
    timing.mark("decoded", monotonic=10.010)
    timing.mark("selected", monotonic=10.025)
    timing.mark("inference_end", monotonic=10.125)

    metrics = timing.to_metrics(publication_monotonic=10.150)

    assert metrics["decode_ms"] == pytest.approx(10)
    assert metrics["coordinator_wait_ms"] == pytest.approx(15)
    assert metrics["inference_ms"] == pytest.approx(100)
    assert metrics["server_total_ms"] == pytest.approx(150)
    assert metrics["frame_age_ms"] == pytest.approx(150)


@pytest.mark.parametrize("capture", [float("nan"), float("inf"), -float("inf")])
def test_non_finite_capture_clock_reports_arrival_age_unavailable(capture):
    timing = FrameTiming(
        received_monotonic=1.0,
        received_wall_ms=10_000.0,
        capture_wall_ms=capture,
    )

    assert timing.to_metrics(2.0)["arrival_age_ms"] is None


def test_capture_clock_outside_skew_tolerance_is_not_trusted():
    timing = FrameTiming(
        received_monotonic=1.0,
        received_wall_ms=10_000.0,
        capture_wall_ms=1_000.0,
        clock_skew_tolerance_ms=2_000.0,
    )

    assert timing.to_metrics(2.0)["arrival_age_ms"] is None


def test_plausible_capture_clock_can_report_arrival_age():
    timing = FrameTiming(
        received_monotonic=1.0,
        received_wall_ms=10_000.0,
        capture_wall_ms=9_875.0,
        clock_skew_tolerance_ms=2_000.0,
    )

    assert timing.to_metrics(1.5)["arrival_age_ms"] == pytest.approx(125.0)


def test_missing_or_reversed_stages_remain_unavailable_not_negative():
    timing = FrameTiming(received_monotonic=10.0)
    timing.mark("tracking_end", monotonic=9.0)
    metrics = timing.to_metrics(10.1)

    assert metrics["decode_ms"] is None
    assert metrics["tracking_ms"] is None
    assert metrics["server_total_ms"] == pytest.approx(100.0)
    assert not any(
        isinstance(value, float) and math.isfinite(value) and value < 0
        for value in metrics.values()
    )
