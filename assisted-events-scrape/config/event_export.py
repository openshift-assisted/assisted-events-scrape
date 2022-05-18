from dataclasses import dataclass
from utils import get_env


DEFAULT_CHUNK_SIZE = "500"


@dataclass
class EventExportConfig:
    chunk_size: int

    @classmethod
    def create_from_env(cls) -> 'EventExportConfig':
        chunk_size = get_env("EVENT_EXPORT_STREAM_CHUNK_SIZE", DEFAULT_CHUNK_SIZE)
        return cls(
            int(chunk_size)
        )
