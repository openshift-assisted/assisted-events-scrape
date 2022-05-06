from dataclasses import dataclass
from utils import get_env

DEFAULT_EVENTS_IDX = ".events"
DEFAULT_CLUSTER_EVENTS_IDX = ".clusters"
DEFAULT_COMPONENT_VERSIONS_EVENTS_IDX = ".component_versions"


@dataclass
class EventStoreConfig:
    EVENTS_INDEX = ".events"
    CLUSTER_EVENTS_INDEX = ".clusters"
    COMPONENT_VERSIONS_EVENTS_INDEX = ".component_versions"

    events_index: str
    cluster_events_index: str
    component_versions_events_index: str

    @classmethod
    def create_from_env(cls) -> 'EventStoreConfig':
        return cls(
            get_env("EVENT_STORE_EVENTS_IDX", default=DEFAULT_EVENTS_IDX),
            get_env("EVENT_STORE_CLUSTER_EVENTS_IDX", default=DEFAULT_CLUSTER_EVENTS_IDX),
            get_env("EVENT_STORE_COMPONENT_VERSIONS_EVENTS_IDX", default=DEFAULT_COMPONENT_VERSIONS_EVENTS_IDX))
