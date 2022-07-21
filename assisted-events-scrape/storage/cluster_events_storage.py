import re
import time
import json
from utils import log, get_event_id
from clients import create_es_client_from_env
from config import ScraperConfig
from events_scrape import InventoryClient
import opensearchpy

from . import process

MAX_EVENTS = 5000
UUID_REGEX = r'[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}'


class ClusterEventsStorage:
    @classmethod
    def create_with_inventory_client(cls, inventory_client: InventoryClient,
                                     config: ScraperConfig) -> 'ClusterEventsStorage':
        es_client = create_es_client_from_env()
        return cls(inventory_client, es_client, config.inventory_url, config.elasticsearch.index)

    def __init__(self, assisted_client, es_client, inventory_url, index):
        self._client = assisted_client
        self._es_client = es_client
        self._inventory_url = inventory_url
        self._index = index
        self._cache_event_count_per_cluster = {}

    def store(self, component_versions, cluster, event_list):
        cluster_id = cluster["id"]

        event_count = len(event_list)
        if event_count > MAX_EVENTS:
            log.info(f"Cluster {cluster_id} has {event_count} event records, logging only {MAX_EVENTS}")
            event_list = event_list[:MAX_EVENTS]

        metadata_json = get_metadata_json(cluster, component_versions)

        cluster_bash_data = process_metadata(metadata_json)
        event_names = get_cluster_object_names(cluster_bash_data)

        events = self.process_events(cluster_bash_data, event_list, event_names)
        self.store_events(events)

        if self.does_cluster_needs_full_update(cluster_id, event_list):
            log.info(f"Cluster {cluster_id} logged events are not same as the event count, logging all clusters events")
            events = self.process_events(cluster_bash_data, event_list, event_names)
            self.store_events(events, only_new_events=False)

    def process_events(self, cluster_bash_data, event_list, event_names):
        for event in event_list[::-1]:
            if process.is_event_skippable(event):
                continue

            cluster_bash_data["no_name_message"] = get_no_name_message(event["message"], event_names)
            cluster_bash_data["inventory_url"] = self._inventory_url

            if "props" in event:
                event["event.props"] = json.loads(event["props"])

            process_event_doc(event, cluster_bash_data)
            yield cluster_bash_data
            for key in event:
                _ = cluster_bash_data.pop(key, None)

    def store_events(self, events, only_new_events=True):
        for event in events:
            doc_id = get_event_id(event)
            ret = self.log_doc(event, doc_id)
            if not ret and only_new_events:
                break

    def does_cluster_needs_full_update(self, cluster_id, event_list):
        # check if cluster is missing past events
        cluster_events_count = self._cache_event_count_per_cluster.get(cluster_id, None)
        relevant_event_count = len([event for event in event_list if not process.is_event_skippable(event)])

        if cluster_events_count and cluster_events_count == relevant_event_count:
            return False
        cluster_events_count_from_db = self.get_cluster_event_count_on_es_db(cluster_id)
        self._cache_event_count_per_cluster[cluster_id] = cluster_events_count_from_db

        if cluster_events_count_from_db < relevant_event_count:
            missing_events = relevant_event_count - cluster_events_count_from_db
            log.info(f"cluster {cluster_id} is missing {missing_events} events")
            return True
        return False

    def get_cluster_event_count_on_es_db(self, cluster_id):
        time.sleep(1)
        results = self._es_client.search(index=self._index,
                                         body={"query": {"match_phrase": {"cluster.id": cluster_id}}})
        return results["hits"]["total"]["value"]

    def log_doc(self, doc, id_):
        try:
            res = self._es_client.create(index=self._index, body=doc, id=id_)
        except opensearchpy.exceptions.ConflictError:
            log.debug("Hit logged event")
            return None
        return res


def get_no_name_message(event_message: str, event_names: list):
    event_message = re.sub(r"^Host \S+:", "", event_message)
    for name in event_names:
        event_message = event_message.replace(name, "Name")
    event_message = re.sub(UUID_REGEX, "UUID", event_message)
    return event_message


def get_cluster_object_names(cluster_bash_data):
    strings_to_remove = []
    for host in cluster_bash_data["cluster"]["hosts"]:
        host_name = host.get("requested_hostname", None)
        if host_name:
            strings_to_remove.append(host_name)
    strings_to_remove.append(cluster_bash_data["cluster"]["name"])
    return strings_to_remove


def process_metadata(metadata_json):
    p = process.GetProcessedMetadataJson(metadata_json)
    return p.get_processed_json()


def process_event_doc(event_data, cluster_bash_data):
    cluster_bash_data.update(event_data)


def get_metadata_json(cluster: dict, component_versions: dict):
    return {'cluster': cluster, **component_versions}
