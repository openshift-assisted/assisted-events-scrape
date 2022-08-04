from dataclasses import dataclass
from typing import List
from copy import deepcopy
import queue
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import dpath.util
from dpath.exceptions import PathNotFound
from retry import retry
from utils import ErrorCounter, Changes, log, get_event_id, get_dict_hash, Anonymizer
from storage import ClusterEventsStorage, ElasticsearchStorage
from events_scrape import InventoryClient
from sentry_sdk import capture_exception
from config import SentryConfig, EventStoreConfig
from assisted_service_client.rest import ApiException

EVENT_CATEGORIES = ["user", "metrics"]


@dataclass
class ClusterEventsWorkerConfig:
    max_workers: int
    sentry: SentryConfig
    error_counter: ErrorCounter
    changes: Changes
    events: EventStoreConfig


class ClusterEventsWorker:
    def __init__(self, config: ClusterEventsWorkerConfig, ai_client: InventoryClient,
                 cluster_events_storage: ClusterEventsStorage, es_store: ElasticsearchStorage):

        self._es_store = es_store
        self._ai_client = ai_client
        self.cluster_events_storage = cluster_events_storage
        self._config = config
        self._executor = None
        self._es_store = es_store

    def process_clusters(self, clusters: List[dict], infraenvs: List[dict]) -> None:
        infraenvs = {item["cluster_id"] : item for item in infraenvs}
        with ThreadPoolExecutor(max_workers=self._config.max_workers) as self._executor:
            cluster_count = len(clusters)
            for cluster in clusters:
                cluster_id = cluster["id"]
                cluster["infra_env"] = {}
                if cluster_id in infraenvs:
                    cluster["infra_env"] = infraenvs[cluster_id]
                self._executor.submit(self.store_events_for_cluster, cluster)
            log.info(f"Sent {cluster_count} clusters for processing...")

    def store_events_for_cluster(self, cluster: dict) -> None:
        try:
            Anonymizer.anonymize_cluster(cluster)
            self._enrich_cluster(cluster)
            log.debug(f"Storing cluster: {cluster}")
            if "hosts" not in cluster or len(cluster["hosts"]) == 0:
                cluster["hosts"] = self.__get_hosts(cluster["id"])
            events = self.__get_events(cluster["id"])
            component_versions = self.__get_versions()
            self._store_normalized_events(component_versions, cluster, events)
            self.cluster_events_storage.store(component_versions, cluster, events)
            self._config.changes.set_changed()
            log.debug(f'Storing events for cluster {cluster["id"]}')
        except Exception as e:
            self.__handle_unexpected_error(e, f'Error while processing cluster {cluster["id"]}')

    @retry(ApiException, delay=1, tries=3, backoff=2, max_delay=4, jitter=1)
    def __get_versions(self):
        return handle_4XX_apiexception(
            self._ai_client.get_versions,
            message_404="Versions not found. This should never happen",
            default_return_value=[]
        )

    @retry(ApiException, delay=1, tries=3, backoff=2, max_delay=4, jitter=1)
    def __get_events(self, cluster_id: str):
        def _internal_get_events():
            return self._ai_client.get_events(cluster_id, categories=EVENT_CATEGORIES)

        return handle_4XX_apiexception(
            _internal_get_events,
            message_404=f"Events for cluster {cluster_id} not found",
            default_return_value=[]
        )

    @retry(ApiException, delay=1, tries=3, backoff=2, max_delay=4, jitter=1)
    def __get_hosts(self, cluster_id: str):
        # If a cluster is not found, then we consider to have 0 hosts. It was probably deleted
        def _internal_get_hosts():
            return self._ai_client.get_cluster_hosts(cluster_id=cluster_id)

        return handle_4XX_apiexception(
            _internal_get_hosts,
            message_404=f"Cluster {cluster_id} not found while retrieving hosts",
            default_return_value=[]
        )

    def __handle_unexpected_error(self, e: Exception, msg: str):
        self._config.error_counter.inc()
        if self._config.sentry.enabled:
            capture_exception(e)
        log.exception(msg)

    def shutdown(self):
        """
        This is needed for python 3.8 and lower. With python 3.9 we can pass a parameter:
        self._executor.shutdown(wait=False, cancel_futures=True)
        """
        if self._executor:
            # Do not accept further tasks
            self._executor.shutdown(wait=False)
            self._drain_queue()

    def _drain_queue(self):
        while True:
            try:
                work_item = self._executor._work_queue.get_nowait()  # pylint: disable=protected-access
            except queue.Empty:
                break
            if work_item:
                work_item.future.cancel()

    def _store_normalized_events(self, component_versions, cluster, event_list):
        try:
            cluster_id_filter = {
                "term": {
                    "cluster_id": cluster["id"]
                }
            }
            cluster_copy = deepcopy(cluster)
            infra_env = cluster_copy.get("infra_env")
            if infra_env:
                del cluster_copy["infra_env"]
                self._es_store.store_changes(
                    index=EventStoreConfig.INFRA_ENVS_EVENTS_INDEX,
                    documents=[infra_env],
                    id_fn=get_dict_hash,
                    filter_by=cluster_id_filter
                )

            self._es_store.store_changes(
                index=EventStoreConfig.CLUSTER_EVENTS_INDEX,
                documents=[cluster_copy],
                id_fn=self._cluster_checksum,
                filter_by=cluster_id_filter
            )
            self._es_store.store_changes(
                index=EventStoreConfig.EVENTS_INDEX,
                documents=event_list,
                id_fn=get_event_id,
                filter_by=cluster_id_filter
            )
            self._es_store.store_changes(
                index=EventStoreConfig.COMPONENT_VERSIONS_EVENTS_INDEX,
                documents=[component_versions],
                id_fn=get_version_hash,
                transform_document_fn=add_timestamp
            )
        except Exception as e:
            self.__handle_unexpected_error(e, f'Error while storing normalized events for cluster {cluster["id"]}')

    def _cluster_checksum(self, doc: dict) -> dict:
        doc_copy = deepcopy(doc)
        log.debug(f"Ignoring fields: <{self._config.events.cluster_events_ignore_fields}>")
        for field in self._config.events.cluster_events_ignore_fields:
            try:
                dpath.util.delete(doc_copy, field, separator=".")
            except PathNotFound:
                # if field is not there, no need to delete it, but don't fail
                pass
        if "hosts" in doc_copy:
            doc_copy["hosts"].sort(key=by_id)
        return get_dict_hash(doc_copy)

    def _enrich_cluster(self, doc: dict):
        doc["cluster_state_id"] = self._cluster_checksum(doc)


def by_id(item: dict) -> str:
    # ID should always be there, if not consider it empty string
    return item.get("id", "")


def add_timestamp(doc: dict) -> dict:
    d = deepcopy(doc)
    # Python can produce timezone information with isoformat()
    # however it would be in the +00:00 form, whereas assisted-service
    # produces it with `Z` notation. To be consistent, we get UTC time
    # without tz info, and append 'Z' in the end
    d["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return d


def get_version_hash(d: dict) -> str:
    return get_dict_hash(d, ["timestamp"])


def handle_4XX_apiexception(f, message_404="", default_return_value=None):
    try:
        return f()
    except ApiException as e:
        if e.status >= 500:
            raise e
        if e.status == 404:
            log.debug(message_404)
        else:
            capture_exception(e)
            log.exception()
    return default_return_value
