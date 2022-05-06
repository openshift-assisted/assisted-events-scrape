from dataclasses import dataclass
from utils import get_env


@dataclass
class SentryConfig:
    enabled: bool
    sentry_dsn: str

    @classmethod
    def create_from_env(cls) -> 'SentryConfig':
        return cls(False, get_env("SENTRY_DSN", default=""))
