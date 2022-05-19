from config import ElasticsearchConfig
from opensearchpy import OpenSearch


def create_es_client_from_env() -> OpenSearch:
    config = ElasticsearchConfig.create_from_env()
    http_auth = None
    if config.username:
        http_auth = (config.username, config.password)
    return OpenSearch(config.host, http_auth=http_auth)
