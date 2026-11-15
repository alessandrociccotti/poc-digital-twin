import json
from pathlib import Path

from digital_twin.events import Event, EventKind, Location


def test_baseline_example_trace():
    path = Path(__file__).with_name("fixtures") / "baseline-small.jsonl"
    events = [Event(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [event.seq for event in events] == list(range(1, len(events) + 1))
    times = [event.time_s for event in events]
    assert times == sorted(times)
    assert [event.part_id for event in events if event.kind == EventKind.PART_COMPLETE] == ["p1", "p2"]

    buffer_times = [
        event.time_s
        for event in events
        if event.part_id == "p2" and event.location == Location.BUFFER_1
    ]
    assert buffer_times == [4, 6]
