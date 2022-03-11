import json
import tempfile

from contextlib import suppress
from assisted_service_client import rest


class EventRepository:
    def __init__(self, assisted_client):
        self.client = assisted_client

    def get_cluster_events(self, cluster_id: str) -> list:
        event_list = []
        with tempfile.NamedTemporaryFile() as temp_event_file:
            self.write_events_file(cluster_id, temp_event_file.name)
            with open(temp_event_file.name) as f:
                event_list = json.load(f)
        return event_list

    def write_events_file(self, cluster_id, output_file):
        with suppress(rest.ApiException):
            self.client.download_cluster_events(cluster_id, output_file, categories=["user", "metrics"])
