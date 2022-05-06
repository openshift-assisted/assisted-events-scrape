from dataclasses import dataclass
from utils import get_env
from .elasticsearch import ElasticsearchConfig
from .sentry import SentryConfig

DEFAULT_ENV_ERRORS_BEFORE_RESTART = "100"
DEFAULT_ENV_MAX_IDLE_MINUTES = "120"
DEFAULT_ENV_N_WORKERS = "5"
MINIMUM_WORKERS = 1


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
