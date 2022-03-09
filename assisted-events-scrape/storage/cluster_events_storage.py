import os
import re
import time
import hashlib
import json
import elasticsearch
from utils import log
from config import ScraperConfig
from events_scrape import InventoryClient
from . import process

MAX_EVENTS = 5000
UUID_REGEX = r'[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}'


class ClusterEventsStorage:
    @staticmethod
    def create_with_inventory_client(inventory_client: InventoryClient,
                                     config: ScraperConfig) -> 'ClusterEventsStorage':
        http_auth = None
        if config.elasticsearch.username:
            http_auth = (config.elasticsearch.username, config.elasticsearch.password)
        es_client = elasticsearch.Elasticsearch(config.elasticsearch.host, http_auth=http_auth)
        return ClusterEventsStorage(
            inventory_client, es_client,
            config.backup_destination, config.inventory_url, config.elasticsearch.index)

    def __init__(self, assisted_client, es_client, backup_destination, inventory_url, index):
        self._client = assisted_client
        self._es_client = es_client
        self._back_destination = backup_destination
        self._inventory_url = inventory_url
        self._index = index
        self._cache_event_count_per_cluster = {}

    def __get_metadata_json(self, cluster: dict):
        d = {'cluster': cluster}
        d.update(self._client.get_versions())
        return d

    def __save_new_backup(self, cluster_id, event_list, metadata_json):
        cluster_backup_directory_path = os.path.join(self._back_destination, f"cluster_{cluster_id}")
        if not os.path.exists(cluster_backup_directory_path):
            os.makedirs(cluster_backup_directory_path)

        event_dest = os.path.join(cluster_backup_directory_path, "events.json")
        with open(event_dest, "w") as f:
            json.dump(event_list, f, indent=4)

        metadata_dest = os.path.join(cluster_backup_directory_path, "metadata.json")
        with open(metadata_dest, "w") as f:
            json.dump(metadata_json, f, indent=4)

    def store(self, cluster, event_list):
        cluster_id = cluster["id"]

        event_count = len(event_list)
        if event_count > MAX_EVENTS:
            log.info(f"Cluster {cluster_id} has {event_count} event records, logging only {MAX_EVENTS}")
            event_list = event_list[:MAX_EVENTS]

        metadata_json = self.__get_metadata_json(cluster)

        if self._back_destination:
            self.__save_new_backup(cluster_id, event_list, metadata_json)

        cluster_bash_data = process_metadata(metadata_json)
        event_names = get_cluster_object_names(cluster_bash_data)

        self.process_and_log_events(cluster_bash_data, event_list, event_names)

        if self.does_cluster_needs_full_update(cluster_id, event_list):
            log.info(f"Cluster {cluster_id} logged events are not same as the event count, logging all clusters events")
            self.process_and_log_events(cluster_bash_data, event_list, event_names, False)

    def process_and_log_events(self, cluster_bash_data, event_list, event_names, only_new_events=True):
        for event in event_list[::-1]:
            if process.is_event_skippable(event):
                continue

            doc_id = get_doc_id(event)
            cluster_bash_data["no_name_message"] = get_no_name_message(event["message"], event_names)
            cluster_bash_data["inventory_url"] = self._inventory_url

            if "props" in event:
                event["event.props"] = json.loads(event["props"])

            process_event_doc(event, cluster_bash_data)
            ret = self.log_doc(cluster_bash_data, doc_id)

            for key in event:
                _ = cluster_bash_data.pop(key, None)

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
        except elasticsearch.exceptions.ConflictError:
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


def get_doc_id(event_json):
    id_str = event_json["event_time"] + event_json["cluster_id"] + event_json["message"]
    _id = int(hashlib.md5(id_str.encode('utf-8')).hexdigest(), 16)
    return str(_id)


def process_event_doc(event_data, cluster_bash_data):
    cluster_bash_data.update(event_data)
