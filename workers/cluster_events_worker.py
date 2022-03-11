from queue import Queue
from threading import Thread
from repositories.cluster_repository import ClusterRepository
from repositories.event_repository import EventRepository
from storage.cluster_events_storage import ClusterEventsStorage
from utils.logger import log
from sentry_sdk import capture_exception
from utils.counters import ErrorCounter
from utils.counters import Changes


class ClusterEventsWorker(Thread):

    def __init__(self, name, cluster_ids_queue: Queue, cluster_repository: ClusterRepository,
                 event_repository: EventRepository, cluster_events_storage: ClusterEventsStorage,
                 error_counter: ErrorCounter, changes: Changes,
                 is_sentry_enabled: bool):
        Thread.__init__(self)
        self.clusters_queue = cluster_ids_queue
        self.name = name
        self.cluster_repository = cluster_repository
        self.event_repository = event_repository
        self.cluster_events_storage = cluster_events_storage
        self.is_sentry_enabled = is_sentry_enabled
        self.error_counter = error_counter
        self.changes = changes

    def run(self):
        while True:
            cluster_id = self.clusters_queue.get()
            try:
                log.info(f"Worker {self.name} Processing cluster {cluster_id}")
                self.store_events_for_cluster(cluster_id)
                log.info(f"Worker {self.name} stored cluster {cluster_id} events")
            finally:
                self.queue.task_done()

    def store_events_for_cluster(self, cluster_id: str) -> None:
        try:
            cluster = self.cluster_repository.get_cluster(cluster_id)
            events = self.event_repository.get_cluster_events(cluster_id)
            self.cluster_events_storage.store(cluster, events)
            self.changes.set_changed()
        except Exception as e:
            self.__handle_unexpected_error(e, f'Error while processing cluster {cluster_id}')

    def __handle_unexpected_error(self, e: Exception, msg: str):
        self.error_counter.inc()
        if self.is_sentry_enabled:
            capture_exception(e)
        log.exception(msg)
