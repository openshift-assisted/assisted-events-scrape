from dataclasses import dataclass
from repositories import ClusterRepository, EventRepository
from utils import ErrorCounter, Changes, log
from storage import ClusterEventsStorage
from sentry_sdk import capture_exception
from config import SentryConfig


@dataclass
class ClusterEventsWorkerConfig:
    sentry: SentryConfig
    error_counter: ErrorCounter
    changes: Changes


class ClusterEventsWorker:

    def __init__(self, config: ClusterEventsWorkerConfig, cluster_repository: ClusterRepository,
                 event_repository: EventRepository, cluster_events_storage: ClusterEventsStorage):

        self.cluster_repository = cluster_repository
        self.event_repository = event_repository
        self.cluster_events_storage = cluster_events_storage
        self.is_sentry_enabled = config.sentry.enabled
        self.error_counter = config.error_counter
        self.changes = config.changes

    def store_events_for_cluster(self, cluster: dict) -> None:
        try:
            if "hosts" not in cluster or len(cluster["hosts"]) == 0:
                cluster["hosts"] = self.cluster_repository.get_cluster_hosts(cluster["id"])
            events = self.event_repository.get_cluster_events(cluster["id"])
            self.cluster_events_storage.store(cluster, events)
            self.changes.set_changed()
        except Exception as e:
            self.__handle_unexpected_error(e, f'Error while processing cluster {cluster["id"]}')

    def __handle_unexpected_error(self, e: Exception, msg: str):
        self.error_counter.inc()
        if self.is_sentry_enabled:
            capture_exception(e)
        log.exception(msg)
