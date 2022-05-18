from dataclasses import dataclass
from storage import DateOffsetOptions


@dataclass
class EventStream:
    name: str
    options: DateOffsetOptions
