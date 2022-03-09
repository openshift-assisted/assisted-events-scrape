from threading import Thread
from repositories import ClusterRepository
from repositories import EventRepository
from storage import ClusterEventsStorage
from utils import log
from sentry_sdk import capture_exception


class ClusterEventsWorker(Thread):

    def __init__(self, config: dict, cluster_repository: ClusterRepository,
                 event_repository: EventRepository, cluster_events_storage: ClusterEventsStorage):

        Thread.__init__(self)
        self.clusters_queue = config["queue"]
        self.name = config["name"]
        self.cluster_repository = cluster_repository
        self.event_repository = event_repository
        self.cluster_events_storage = cluster_events_storage
        self.is_sentry_enabled = False
        if "sentry" in config and "enabled" in config["sentry"]:
            self.is_sentry_enabled = config["sentry"]["enabled"]
        self.error_counter = config["error_counter"]
        self.changes = config["changes"]

    def run(self):
        while True:
            self.consume_queue()

    def consume_queue(self):
        cluster = self.clusters_queue.get()
        try:
            log.info(f'Worker {self.name} Processing cluster {cluster["id"]}')
            self.store_events_for_cluster(cluster)
            log.info(f'Worker {self.name} stored cluster {cluster["id"]} events')
        finally:
            self.clusters_queue.task_done()

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
