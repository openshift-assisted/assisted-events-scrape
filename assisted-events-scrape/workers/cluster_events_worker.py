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
from process import reshape_host
from storage import ClusterEventsStorage, ElasticsearchStorage
from events_scrape import InventoryClient
from sentry_sdk import capture_exception
from config import SentryConfig, EventStoreConfig
from assisted_service_client.rest import ApiException

EVENT_CATEGORIES = ["user", "metrics"]
MAX_HOSTS_COUNT = 50


class ResourceNotFoundException(Exception):
    pass


class ClusterBlacklistedException(Exception):
    pass


class ClusterTooLargeException(Exception):
    pass


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
        self._infra_envs = {}
        self._blacklisted_names = ["perf-test"]

    def process_clusters(self, clusters: List[dict]) -> None:
        infraenvs = self._ai_client.infra_envs_list()
        self._infra_envs = {item["id"] : item for item in infraenvs}

        with ThreadPoolExecutor(max_workers=self._config.max_workers) as self._executor:
            cluster_count = len(clusters)
            for cluster in clusters:
                self._executor.submit(self.store_events_for_cluster, cluster)
            log.info(f"Sent {cluster_count} clusters for processing...")

    def store_events_for_cluster(self, cluster: dict) -> None:
        try:
            if self._is_blacklisted(cluster):
                raise ClusterBlacklistedException(f"Cluster ID {cluster['id']} is blacklisted.")
            Anonymizer.anonymize_cluster(cluster)
            self._enrich_cluster(cluster)

            if len(cluster["hosts"]) > MAX_HOSTS_COUNT:
                raise ClusterTooLargeException(
                    f"Cluster ID {cluster['id']} has too many hosts ({len(cluster['hosts'])}>{MAX_HOSTS_COUNT})."
                )

            log.debug(f"Storing cluster: {cluster}")

            events = self.__get_events(cluster["id"])
            component_versions = self.__get_versions()

            hosts_infra_envs = self._get_hosts_infraenvs(cluster["hosts"])
            infra_envs = self.__get_infra_envs_list()

            _anonymize_infra_envs(hosts_infra_envs, infra_envs)

            self._store_normalized_events(component_versions, cluster, events, infra_envs)
            self.cluster_events_storage.store(component_versions, cluster, events, hosts_infra_envs)
            self._config.changes.set_changed()
            log.debug(f'Storing events for cluster {cluster["id"]}')
        except (ClusterTooLargeException, ClusterBlacklistedException) as e:
            log.warning(str(e))
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

    def _get_hosts_infraenvs(self, hosts):
        hosts_infra_envs = []
        hosts_infra_envs = self.__get_infra_envs(
            [host["infra_env_id"] for host in hosts
             if host and "infra_env_id" in host and host["infra_env_id"] is not None]
        )
        self.__set_infra_envs(hosts_infra_envs)
        return hosts_infra_envs

    def __get_infra_envs_list(self) -> List[dict]:
        return list(self._infra_envs.values())

    def __set_infra_envs(self, infra_envs: dict):
        for key in infra_envs:
            self._infra_envs[key] = infra_envs[key]

    def __get_infra_envs(self, infra_env_ids: List[str]) -> dict:
        infra_envs = {}
        for infra_env_id in infra_env_ids:
            try:
                infra_env = self.__get_cached_infra_env(infra_env_id)
                infra_envs[infra_env["id"]] = deepcopy(infra_env)
            except ResourceNotFoundException as e:
                log.exception(f"InfraEnv not found: {e}")

        return infra_envs

    def __get_cached_infra_env(self, infra_env_id: str) -> dict:
        infra_env = self._infra_envs.get(infra_env_id)
        if infra_env:
            return infra_env
        infra_env = self.__get_infra_env(infra_env_id)
        if not infra_env:
            raise ResourceNotFoundException(f"Infra env {infra_env_id} not found")
        self._infra_envs[infra_env["id"]] = infra_env
        return infra_env

    @retry(ApiException, delay=1, tries=3, backoff=2, max_delay=4, jitter=1)
    def __get_infra_env(self, infra_env_id: str):
        def _internal_get_infraenv():
            infra_env = self._ai_client.get_infra_env(infra_env_id=infra_env_id)
            if infra_env:
                return infra_env.to_dict()
            return None

        return handle_4XX_apiexception(
            _internal_get_infraenv,
            message_404=f"InfraEnv {infra_env_id} not found",
            default_return_value=None
        )

    def __handle_unexpected_error(self, e: Exception, msg: str):
        self._config.error_counter.inc()
        if self._config.sentry.enabled:
            capture_exception(e)
        log.exception(f"Unexpected error: {msg}")

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

    def _store_normalized_events(self, component_versions, cluster, event_list, infra_envs):
        try:
            cluster_id_filter = {
                "term": {
                    "cluster_id": cluster["id"]
                }
            }

            self._es_store.store_changes(
                index=EventStoreConfig.INFRA_ENVS_EVENTS_INDEX,
                documents=infra_envs,
                id_fn=get_dict_hash,
                filter_by=cluster_id_filter
            )

            self._es_store.store_changes(
                index=EventStoreConfig.CLUSTER_EVENTS_INDEX,
                documents=[cluster],
                id_fn=self._cluster_checksum,
                filter_by=cluster_id_filter
            )
            self._es_store.store_changes(
                index=EventStoreConfig.EVENTS_INDEX,
                documents=event_list,
                id_fn=get_event_id,
                transform_document_fn=add_event_id,
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

    def add_cluster_state_id(self, doc: dict):
        doc_copy = deepcopy(doc)
        doc_copy["cluster_state_id"] = self._cluster_checksum(doc)
        return doc_copy

    def _enrich_cluster(self, cluster: dict):
        if "hosts" not in cluster or len(cluster["hosts"]) == 0:
            cluster["hosts"] = self.__get_hosts(cluster["id"])
        cluster["cluster_state_id"] = self._cluster_checksum(cluster)
        for host in cluster["hosts"]:
            reshape_host(host)

    def _is_blacklisted(self, cluster: dict) -> bool:
        return "name" in cluster and cluster["name"] in self._blacklisted_names


def _anonymize_infra_envs(hosts_infra_envs, infra_envs):
    for infra_env in hosts_infra_envs:
        Anonymizer.anonymize_infra_env(infra_env)
    for infra_env in infra_envs:
        Anonymizer.anonymize_infra_env(infra_env)


def by_id(item: dict) -> str:
    """
    This function is used to sort host array by id.
    `id` field should always be present, if not, we don't want to panic and we
    just return empty string
    """
    return item.get("id", "")


def add_timestamp(doc: dict) -> dict:
    d = deepcopy(doc)
    # Python can produce timezone information with isoformat()
    # however it would be in the +00:00 form, whereas assisted-service
    # produces it with `Z` notation. To be consistent, we get UTC time
    # without tz info, and append 'Z' in the end
    d["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return d


def add_event_id(doc: dict) -> dict:
    d = deepcopy(doc)
    d["event_id"] = get_event_id(doc)
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
