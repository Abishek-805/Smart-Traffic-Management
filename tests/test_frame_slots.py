from server.frame_slots import LatestFrameSlots


DIRECTIONS = ("north", "east", "south", "west")


def packet(direction: str, sequence: int, received_at: float = 0.0) -> dict:
    return {
        "backend_receive_monotonic": received_at,
        "payload": {"direction": direction, "frame_id": f"{direction}-{sequence}"},
    }


def test_each_direction_keeps_exactly_one_pending_packet():
    slots = LatestFrameSlots(DIRECTIONS)

    for sequence in range(100):
        slots.offer("north", packet("north", sequence))

    assert slots.pending_count == 1
    assert slots.counters["north"].offered == 100
    assert slots.counters["north"].replaced == 99
    selected = slots.select_due(now=0.0, max_items=1)
    assert selected[0]["payload"]["frame_id"] == "north-99"


def test_round_robin_selection_prevents_a_busy_direction_from_leading_forever():
    slots = LatestFrameSlots(DIRECTIONS)
    first_selected = []

    for tick in range(4):
        for direction in DIRECTIONS:
            slots.offer(direction, packet(direction, tick, received_at=float(tick)))
        selected = slots.select_due(now=float(tick), max_items=1)
        first_selected.append(selected[0]["payload"]["direction"])

    assert first_selected == list(DIRECTIONS)
    assert all(slots.counters[direction].selected == 1 for direction in DIRECTIONS)


def test_stale_packet_is_dropped_without_becoming_an_observation():
    slots = LatestFrameSlots(DIRECTIONS, stale_after_sec=2.5)
    slots.offer("south", packet("south", 1, received_at=5.0))

    assert slots.select_due(now=7.6, max_items=4) == []
    assert slots.pending_count == 0
    assert slots.counters["south"].stale_dropped == 1
    assert slots.counters["south"].processed == 0


def test_processing_and_failures_are_counted_per_direction():
    slots = LatestFrameSlots(DIRECTIONS)

    slots.mark_processed("east")
    slots.mark_failure("east", "decode")
    slots.mark_failure("east", "inference")

    counters = slots.snapshot()["east"]
    assert counters == {
        "offered": 0,
        "selected": 0,
        "processed": 1,
        "replaced": 0,
        "stale_dropped": 0,
        "decode_failed": 1,
        "inference_failed": 1,
    }
