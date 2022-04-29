import os
from dataclasses import dataclass

DEFAULT_EVENTS_IDX = ".events"
DEFAULT_CLUSTER_EVENTS_IDX = ".clusters"
DEFAULT_COMPONENT_VERSIONS_EVENTS_IDX = ".component_versions"
DEFAULT_ENV_ERRORS_BEFORE_RESTART = "100"
DEFAULT_ENV_MAX_IDLE_MINUTES = "120"
DEFAULT_ENV_N_WORKERS = "5"
MINIMUM_WORKERS = 1


@dataclass
class EventStoreConfig:
    events_index: str
    cluster_events_index: str
    component_versions_events_index: str

    @classmethod
    def create_from_env(cls) -> 'EventStoreConfig':
        return cls(
            get_env("EVENT_STORE_EVENTS_IDX", default=DEFAULT_EVENTS_IDX),
            get_env("EVENT_STORE_CLUSTER_EVENTS_IDX", default=DEFAULT_CLUSTER_EVENTS_IDX),
            get_env("EVENT_STORE_COMPONENT_VERSIONS_EVENTS_IDX", default=DEFAULT_COMPONENT_VERSIONS_EVENTS_IDX))


@dataclass
class SentryConfig:
    enabled: bool
    sentry_dsn: str

    @classmethod
    def create_from_env(cls) -> 'SentryConfig':
        return cls(False, get_env("SENTRY_DSN", default=""))


@dataclass
class ElasticsearchConfig:
    host: str
    index: str
    username: str
    password: str

    @classmethod
    def create_from_env(cls) -> 'ElasticsearchConfig':
        return cls(
            get_env("ES_SERVER", mandatory=True),
            get_env("ES_INDEX", mandatory=True),
            get_env("ES_USER"),
            get_env("ES_PASS"))


@dataclass
class ScraperConfig:
    inventory_url: str
    offline_token: str
    sentry: SentryConfig
    elasticsearch: ElasticsearchConfig
    max_idle_minutes: int
    errors_before_restart: int
    n_workers: int

    @classmethod
    def create_from_env(cls) -> 'ScraperConfig':
        n_workers = max(MINIMUM_WORKERS, int(get_env("N_WORKERS", default=DEFAULT_ENV_N_WORKERS)))
        return cls(
            get_env("ASSISTED_SERVICE_URL"),
            get_env("OFFLINE_TOKEN"),
            SentryConfig.create_from_env(),
            ElasticsearchConfig.create_from_env(),
            int(get_env("MAX_IDLE_MINUTES", default=DEFAULT_ENV_MAX_IDLE_MINUTES)),
            int(get_env("ERRORS_BEFORE_RESTART", default=DEFAULT_ENV_ERRORS_BEFORE_RESTART)),
            n_workers)


def get_env(key, mandatory=False, default=None):
    res = os.environ.get(key, default)
    if res == "":
        res = default

    if res is not None:
        res = res.strip()
    elif mandatory:
        raise ValueError(f'Mandatory environment variable is missing: {key}')

    return res
