from assisted_service_client import rest


class ClusterRepository:
    def __init__(self, assisted_client):
        self.client = assisted_client

    def list_clusters(self):
        return self.client.clusters_list()

    def get_cluster_hosts(self, cluster_id: str) -> list:
        hosts = []
        try:
            hosts = self.client.get_cluster_hosts(cluster_id=cluster_id)
        except rest.ApiException as e:
            if e.reason != "Not Found":
                raise
        return hosts
