from dataclasses import dataclass
from utils import get_env


@dataclass
class ElasticsearchConfig:
    host: str
    index_prefix: str
    username: str
    password: str

    @classmethod
    def create_from_env(cls) -> 'ElasticsearchConfig':
        return cls(
            get_env("ES_SERVER"),
            get_env("ES_INDEX_PREFIX"),
            get_env("ES_USER"),
            get_env("ES_PASS"))
