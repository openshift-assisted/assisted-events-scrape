import os
from dataclasses import dataclass

DEFAULT_ENV_ERRORS_BEFORE_RESTART = "100"
DEFAULT_ENV_MAX_IDLE_MINUTES = "120"
DEFAULT_ENV_N_WORKERS = "5"
MINIMUM_WORKERS = 1


@dataclass
class SentryConfig:
    enabled: bool
    sentry_dsn: str

    @staticmethod
    def create_from_env() -> 'SentryConfig':
        return SentryConfig(False, get_env("SENTRY_DSN", default=""))


@dataclass
class ElasticsearchConfig:
    host: str
    index: str
    username: str
    password: str

    @staticmethod
    def create_from_env() -> 'ElasticsearchConfig':
        return ElasticsearchConfig(
            get_env("ES_SERVER", mandatory=True),
            get_env("ES_INDEX", mandatory=True),
            get_env("ES_USER"),
            get_env("ES_PASS"))


@dataclass
class ScraperConfig:
    inventory_url: str
    backup_destination: str
    offline_token: str
    sentry: SentryConfig
    elasticsearch: ElasticsearchConfig
    max_idle_minutes: int
    errors_before_restart: int
    n_workers: int

    @staticmethod
    def create_from_env() -> 'ScraperConfig':
        n_workers = max(MINIMUM_WORKERS, int(get_env("N_WORKERS", default=DEFAULT_ENV_N_WORKERS)))
        return ScraperConfig(
            get_env("ASSISTED_SERVICE_URL"),
            get_env("BACKUP_DESTINATION"),
            get_env("OFFLINE_TOKEN", mandatory=True),
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
