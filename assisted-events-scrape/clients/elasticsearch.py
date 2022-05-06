from config import ElasticsearchConfig
from elasticsearch import Elasticsearch


def create_es_client_from_env() -> Elasticsearch:
    config = ElasticsearchConfig.create_from_env()
    http_auth = None
    if config.username:
        http_auth = (config.username, config.password)
    return Elasticsearch(config.host, http_auth=http_auth)
