#!/usr/bin/env python3

import os
import time
import urllib3
import logging
import elasticsearch
import sentry_sdk

from queue import Queue

from .assisted_service_api import ClientFactory
from utils.logger import log
from repositories.cluster_repository import ClusterRepository
from repositories.event_repository import EventRepository
from storage.cluster_events_storage import ClusterEventsStorage
from workers.cluster_events_worker import ClusterEventsWorker
from utils.counters import ErrorCounter
from utils.counters import Changes

N_WORKERS = 5
RETRY_INTERVAL = 60 * 5

DEFAULT_ENV_ERRORS_BEFORE_RESTART = "100"
DEFAULT_ENV_MAX_IDLE_MINUTES = "120"
DEFAULT_ENV_MEMORY_CACHE_TTL = "600"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

es_logger = logging.getLogger('elasticsearch')
es_logger.setLevel(logging.WARNING)


class ScrapeEvents:
    def __init__(self, inventory_url: str, offline_token: str, index: str, es_server: str, es_user: str,
                 es_pass: str, backup_destination: str, is_sentry_enabled: bool, max_idle_minutes: int,
                 errors_before_restart: int, memory_cache_ttl: int):

        self.inventory_url = inventory_url
        self.client = ClientFactory.create_client(url=self.inventory_url, offline_token=offline_token)
        http_auth = None

        if es_user:
            http_auth = (es_user, es_pass)
        es_client = elasticsearch.Elasticsearch(es_server, http_auth=http_auth)
        self.is_sentry_enabled = is_sentry_enabled
        self.max_idle_minutes = max_idle_minutes
        self.errors_before_restart = errors_before_restart
        self.cluster_repo = ClusterRepository(self.client, memory_cache_ttl)
        self.event_repo = EventRepository(self.client)

        if backup_destination and not os.path.exists(backup_destination):
            os.makedirs(backup_destination)

        self.cluster_events_storage = ClusterEventsStorage(
            self.client, es_client,
            backup_destination, inventory_url, index)

        self.cluster_ids_queue = Queue()
        self.error_counter = ErrorCounter()
        self.changes = Changes()
        self.start_workers(N_WORKERS)

    def start_workers(self, n_workers: int) -> None:
        for n in range(n_workers):
            worker = ClusterEventsWorker(name=f"Worker {n}", cluster_ids_queue=self.cluster_ids_queue,
                                         cluster_repository=self.cluster_repo, event_repository=self.event_repo,
                                         cluster_events_storage=self.cluster_events_storage,
                                         error_counter=self.error_counter, changes=self.changes,
                                         is_sentry_enabled=self.is_sentry_enabled)
            worker.daemon = True
            worker.start()

    def is_idle(self):
        return not self.changes.has_changed_in_last_minutes(self.max_idle_minutes)

    def has_too_many_unexpected_errors(self):
        return self.error_counter.get_errors() > self.errors_before_restart

    def run_service(self):

        cluster_ids = self.cluster_repo.list_cluster_ids()

        if not cluster_ids:
            log.warning(f'No clusters were found, waiting {RETRY_INTERVAL / 60} min')
            time.sleep(RETRY_INTERVAL)
            return None

        cluster_count = len(cluster_ids)
        for cluster_id in cluster_ids:
            self.cluster_ids_queue.put(cluster_id)
        log.info(f"Added {cluster_count} cluster IDs to queue, joining queue...")
        self.cluster_ids_queue.join()
        log.info("Finish syncing all clusters - sleeping 30 seconds")
        time.sleep(30)


def get_env(key, mandatory=False, default=None):
    res = os.environ.get(key, default)

    if res is not None:
        res = res.strip()
    elif mandatory:
        raise ValueError(f'Mandatory environment variable is missing: {key}')

    return res


def handle_arguments():
    return {
        "assisted_service_url": get_env("ASSISTED_SERVICE_URL"),
        "offline_token": get_env("OFFLINE_TOKEN", mandatory=True),
        "es_server": get_env("ES_SERVER", mandatory=True),
        "es_user": get_env("ES_USER"),
        "es_pass": get_env("ES_PASS"),
        "index": get_env("ES_INDEX", mandatory=True),
        "backup_destination": get_env("BACKUP_DESTINATION"),
        "sentry_dsn": get_env("SENTRY_DSN", default=""),
        "max_idle_minutes": get_env("MAX_IDLE_MINUTES", default=DEFAULT_ENV_MAX_IDLE_MINUTES),
        "errors_before_restart": get_env("ERRORS_BEFORE_RESTART", default=DEFAULT_ENV_ERRORS_BEFORE_RESTART),
        "memory_cache_ttl": get_env("MEMORY_CACHE_TTL", default=DEFAULT_ENV_MEMORY_CACHE_TTL)
    }


def initSentry(sentry_dsn):
    if sentry_dsn != "":
        sentry_sdk.init(
            sentry_dsn
        )
        return True
    return False


def main():
    args = handle_arguments()
    is_sentry_enabled = initSentry(args["sentry_dsn"])
    should_run = True
    while should_run:
        scrape_events = ScrapeEvents(inventory_url=args["assisted_service_url"],
                                     offline_token=args["offline_token"],
                                     index=args["index"],
                                     es_server=args["es_server"],
                                     es_user=args["es_user"],
                                     es_pass=args["es_pass"],
                                     backup_destination=args["backup_destination"],
                                     is_sentry_enabled=is_sentry_enabled,
                                     max_idle_minutes=int(args["max_idle_minutes"]),
                                     errors_before_restart=int(args["errors_before_restart"]),
                                     memory_cache_ttl=int(args["memory_cache_ttl"]))

        scrape_events.run_service()
        should_run = scrape_events.is_idle() or scrape_events.has_too_many_unexpected_errors()
