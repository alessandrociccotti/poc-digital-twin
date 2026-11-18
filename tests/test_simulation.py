from collections import defaultdict
from dataclasses import asdict, replace

from digital_twin.events import Event, EventKind, Location
from digital_twin.simulation.model import SimulationConfig, run_simulation


def test_fixed_baseline_matches_analytical_completion_times():
    result = run_simulation(SimulationConfig())
    summary = result.summary()
    assert summary["arrivals"] == 36
    assert summary["completed"] == 35
    assert summary["work_in_progress"] == 1
    assert result.unfinished_parts == {"p36": "cnc"}
    completions = [e.time_s for e in result.events if e.kind == EventKind.PART_COMPLETE]
    assert completions == list(range(180, 3600, 100))
    assert all(e.time_s < 3600 for e in result.events)


def test_overloaded_line_preserves_capacity_fifo_and_blocking():
    config = SimulationConfig(arrival_interval_s=1, casting_time_s=1, cnc_time_s=10,
                              leak_test_time_s=20, duration_s=100)
    result = run_simulation(config)
    queues = defaultdict(list)
    active = {}
    finished = {}
    blocked = []
    for expected_seq, event in enumerate(result.events, 1):
        assert event.seq == expected_seq
        assert Event(**asdict(event)) == event
        if event.kind == EventKind.PROCESS_START:
            assert event.location not in active
            active[event.location] = event.part_id
        elif event.kind == EventKind.PROCESS_END:
            assert active.pop(event.location) == event.part_id
            finished[event.part_id] = event.time_s
        elif event.kind == EventKind.BUFFER_ENTER:
            queues[event.location].append(event.part_id)
            capacity = config.buffer_1_capacity if event.location == Location.BUFFER_1 else config.buffer_2_capacity
            assert len(queues[event.location]) <= capacity
            blocked.append(event.time_s - finished[event.part_id])
        elif event.kind == EventKind.BUFFER_EXIT:
            assert queues[event.location].pop(0) == event.part_id
    assert max(blocked) > 0
    summary = result.summary()
    assert summary["arrivals"] == summary["completed"] + summary["work_in_progress"]


def test_stochastic_runs_are_reproducible():
    config = SimulationConfig(processing_cv=0.1)
    first = run_simulation(config)
    assert first == run_simulation(config)
    assert first.events != run_simulation(replace(config, seed=43)).events
