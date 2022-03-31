EVENT_CATEGORIES = ["user", "metrics"]


class EventRepository:
    def __init__(self, assisted_client):
        self._client = assisted_client

    def get_cluster_events(self, cluster_id: str) -> list:
        return self._client.get_events(cluster_id, categories=EVENT_CATEGORIES)
