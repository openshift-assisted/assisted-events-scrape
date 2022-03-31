#!/usr/bin/env python3

import sys
import time
import logging
import signal
import urllib3
import sentry_sdk

from events_scrape import ClientFactory
from repositories import ClusterRepository, EventRepository
from storage import ClusterEventsStorage
from workers import ClusterEventsWorker, ClusterEventsWorkerConfig
from utils import ErrorCounter, Changes, log
from config import ScraperConfig

WAIT_TIME = 60

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

es_logger = logging.getLogger('elasticsearch')
es_logger.setLevel(logging.WARNING)


class ScrapeEvents:
    def __init__(self, config: ScraperConfig):
        self._client = ClientFactory.create_client(url=config.inventory_url, offline_token=config.offline_token)
        self._cluster_events_storage = ClusterEventsStorage.create_with_inventory_client(self._client, config)

        self._cluster_repo = ClusterRepository(self._client)
        self._event_repo = EventRepository(self._client)

        self._errors_before_restart = config.errors_before_restart
        self._max_idle_minutes = config.max_idle_minutes
        self._changes = Changes()
        self._error_counter = ErrorCounter()
        self._shutdown = False
        worker_config = ClusterEventsWorkerConfig(
            config.n_workers,
            config.sentry,
            self._error_counter,
            self._changes
        )
        self._worker = ClusterEventsWorker(worker_config, self._cluster_repo, self._event_repo,
                                           self._cluster_events_storage)

    def is_idle(self):
        return not self._changes.has_changed_in_last_minutes(self._max_idle_minutes)

    def is_shutting_down(self):
        return self._shutdown

    def has_too_many_unexpected_errors(self):
        return self._error_counter.get_errors() > self._errors_before_restart

    def run_service(self):
        clusters = self._cluster_repo.list_clusters()

        if not clusters:
            log.warning("No clusters were found.")
            return None
        self._worker.process_clusters(clusters)
        log.info("Finish syncing all clusters")

    def shutdown(self, sig, _):
        logging.info(f"Captured signal {sig}, shutting down")
        self._shutdown = True
        self._worker.shutdown()
        logging.info("Graceful shutdown handled")


def init_sentry(sentry_dsn):
    if sentry_dsn != "":
        sentry_sdk.init(
            sentry_dsn
        )
        return True
    return False


def handle_shutdown(handler):
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


def main():
    config = ScraperConfig.create_from_env()
    config.sentry.enabled = init_sentry(config.sentry.sentry_dsn)

    scrape_events = ScrapeEvents(config)
    handle_shutdown(scrape_events.shutdown)
    should_run = True
    while should_run:
        scrape_events.run_service()

        if scrape_events.is_shutting_down():
            should_run = False
        elif scrape_events.is_idle():
            log.error("Scraping is idle, exiting...")
            should_run = False
        elif scrape_events.has_too_many_unexpected_errors():
            log.error("Too many unexpected errors, exiting")
            should_run = False
        log.info(f"Waiting {WAIT_TIME} seconds")
        time.sleep(WAIT_TIME)
    sys.exit(1)
