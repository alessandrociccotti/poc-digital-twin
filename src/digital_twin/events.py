"""Shared event contract for baseline JSONL traces."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


class EventKind(StrEnum):
    ARRIVAL = "arrival"
    PROCESS_START = "process_start"
    PROCESS_END = "process_end"
    BUFFER_ENTER = "buffer_enter"
    BUFFER_EXIT = "buffer_exit"
    PART_COMPLETE = "part_complete"


class Location(StrEnum):
    LINE = "line"
    CASTING = "casting"
    BUFFER_1 = "buffer_1"
    CNC = "cnc"
    BUFFER_2 = "buffer_2"
    LEAK_TEST = "leak_test"


EVENT_LOCATIONS = {
    EventKind.ARRIVAL: {Location.LINE},
    EventKind.PROCESS_START: {Location.CASTING, Location.CNC, Location.LEAK_TEST},
    EventKind.PROCESS_END: {Location.CASTING, Location.CNC, Location.LEAK_TEST},
    EventKind.BUFFER_ENTER: {Location.BUFFER_1, Location.BUFFER_2},
    EventKind.BUFFER_EXIT: {Location.BUFFER_1, Location.BUFFER_2},
    EventKind.PART_COMPLETE: {Location.LEAK_TEST},
}


@dataclass(frozen=True, slots=True)
class Event:
    seq: int
    time_s: float
    kind: EventKind
    part_id: str
    location: Location
    source: str

    def __post_init__(self) -> None:
        if type(self.seq) is not int or self.seq < 1:
            raise ValueError("seq must be a positive integer")
        if type(self.time_s) not in (int, float) or not 0 <= self.time_s or not isfinite(self.time_s):
            raise ValueError("time_s must be finite and nonnegative")
        for name in ("part_id", "source"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a nonempty string")
        kind = EventKind(self.kind)
        location = Location(self.location)
        if location not in EVENT_LOCATIONS[kind]:
            raise ValueError(f"{location} is invalid for {kind}")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "location", location)
