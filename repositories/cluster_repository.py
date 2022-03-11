from datetime import datetime, timedelta
from typing import Optional
import threading
from assisted_service_client import rest


class ClusterRepository:
    def __init__(self, assisted_client, ttl=600):
        self.client = assisted_client
        self.cluster_list_lock = threading.Lock()
        self.ttl = ttl
        self.clusters = None
        self.expires_at = None

    def list_cluster_ids(self):
        self.__update_cluster_list_if_expired()
        return [*self.clusters]

    def get_cluster(self, cluster_id: str, try_upstream=True) -> Optional[dict]:
        self.__update_cluster_list_if_expired()
        cluster = self.__get_cluster(cluster_id)
        if cluster is not None:
            return cluster
        # if not found, try upstream
        if try_upstream:
            self.__update_cluster_list()
            return self.get_cluster(cluster_id, try_upstream=False)
        return None

    def __get_cluster(self, cluster_id: str) -> Optional[dict]:
        if cluster_id not in self.clusters:
            return None
        # TODO: cache calls to hosts
        if "hosts" not in self.clusters[cluster_id] or len(self.clusters[cluster_id]["hosts"]) < 1:
            try:
                self.clusters[cluster_id]["hosts"] = self.client.get_cluster_hosts(cluster_id=cluster_id)
            except rest.ApiException as e:
                if e.reason != "Not Found":
                    raise
                self.clusters[cluster_id]["hosts"] = []
        return self.clusters[cluster_id]

    def __update_cluster_list_if_expired(self) -> None:
        if self.__is_cache_expired() or (self.clusters is None):
            self.__update_cluster_list()

    def __update_cluster_list(self) -> None:
        with self.cluster_list_lock:
            cluster_list = self.client.clusters_list()
            self.clusters = self.__list_to_dic(cluster_list)
            self.__set_ttl(self.ttl)

    def __is_cache_expired(self) -> bool:
        return self.expires_at is None or datetime.now() > self.expires_at

    def __list_to_dic(self, list) -> dict:
        return {cluster["id"]: cluster for cluster in list}

    def __set_ttl(self, ttl) -> None:
        self.expires_at = datetime.now() + timedelta(seconds=ttl)
