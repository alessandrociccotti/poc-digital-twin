"""Reference plant with finite FIFO buffers and blocking after service."""

from dataclasses import asdict, dataclass
from math import isfinite, log, sqrt
from random import Random

import simpy

from digital_twin.events import Event, EventKind, Location


@dataclass(frozen=True)
class SimulationConfig:
    arrival_interval_s: float = 100
    casting_time_s: float = 60
    cnc_time_s: float = 90
    leak_test_time_s: float = 30
    buffer_1_capacity: int = 2
    buffer_2_capacity: int = 2
    duration_s: float = 3600
    processing_cv: float = 0
    seed: int = 42

    def __post_init__(self):
        for name in (
            "arrival_interval_s", "casting_time_s", "cnc_time_s",
            "leak_test_time_s", "duration_s"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        for name in ("buffer_1_capacity", "buffer_2_capacity"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if type(self.processing_cv) not in (int, float) or not isfinite(self.processing_cv) or self.processing_cv < 0:
            raise ValueError("processing_cv must be finite and nonnegative")
        if type(self.seed) is not int:
            raise ValueError("seed must be an integer")


@dataclass
class SimulationResult:
    config: SimulationConfig
    events: list[Event]
    unfinished_parts: dict[str, str]

    def summary(self):
        arrivals = sum(event.kind == EventKind.ARRIVAL for event in self.events)
        completed = sum(event.kind == EventKind.PART_COMPLETE for event in self.events)
        return {
            "schema_version": 1,
            "source": "simulated_reference",
            "config": asdict(self.config),
            "interval": "[0, duration_s)",
            "arrivals": arrivals,
            "completed": completed,
            "work_in_progress": len(self.unfinished_parts),
            "unfinished_parts": self.unfinished_parts,
        }


class _Buffer:
    def __init__(self, env, capacity, location):
        self.items = simpy.Store(env)
        self.slots = simpy.Resource(env, capacity=capacity)
        self.location = location


def run_simulation(config: SimulationConfig) -> SimulationResult:
    """Run an initially empty line over [0, duration_s), preserving unfinished parts."""
    env = simpy.Environment()
    upstream = simpy.Store(env)
    buffer_1 = _Buffer(env, config.buffer_1_capacity, Location.BUFFER_1)
    buffer_2 = _Buffer(env, config.buffer_2_capacity, Location.BUFFER_2)
    events = []
    positions = {}

    def emit(kind, part, location):
        events.append(Event(
            seq=len(events) + 1, time_s=env.now, kind=kind,
            part_id=part, location=location, source="simulated_reference",
        ))
        if kind == EventKind.PART_COMPLETE:
            del positions[part]
        else:
            positions[part] = location.value

    def arrivals():
        number = 1
        while True:
            part = f"p{number}"
            emit(EventKind.ARRIVAL, part, Location.LINE)
            upstream.put((part, None))
            number += 1
            yield env.timeout(config.arrival_interval_s)

    def station(location, mean, incoming, outgoing, stream_seed):
        random = Random(stream_seed)
        sigma = sqrt(log(1 + config.processing_cv ** 2))
        mu = log(mean) - sigma ** 2 / 2
        while True:
            part, slot = yield incoming.items.get() if isinstance(incoming, _Buffer) else incoming.get()
            if isinstance(incoming, _Buffer):
                emit(EventKind.BUFFER_EXIT, part, incoming.location)
                incoming.slots.release(slot)
            emit(EventKind.PROCESS_START, part, location)
            duration = mean
            if config.processing_cv:
                duration = random.lognormvariate(mu, sigma)
            yield env.timeout(duration)
            emit(EventKind.PROCESS_END, part, location)
            if outgoing is None:
                emit(EventKind.PART_COMPLETE, part, location)
            else:
                # Retain the finished part at the station until a buffer slot is granted.
                slot = outgoing.slots.request()
                yield slot
                emit(EventKind.BUFFER_ENTER, part, outgoing.location)
                outgoing.items.put((part, slot))

    env.process(arrivals())
    env.process(station(Location.CASTING, config.casting_time_s, upstream, buffer_1, config.seed))
    env.process(station(Location.CNC, config.cnc_time_s, buffer_1, buffer_2, config.seed + 1))
    env.process(station(Location.LEAK_TEST, config.leak_test_time_s, buffer_2, None, config.seed + 2))
    env.run(until=config.duration_s)
    return SimulationResult(config, events, dict(positions))
