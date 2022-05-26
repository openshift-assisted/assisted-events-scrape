from dataclasses import dataclass
from utils import get_env, log


DEFAULT_S3_ENDPOINT_PROTOCOL = "https://"


@dataclass
class ObjectStorageConfig:
    access_key: str
    secret_key: str
    endpoint_url: str
    bucket: str

    @classmethod
    def create_from_env(cls) -> 'ObjectStorageConfig':
        endpoint = get_env("AWS_S3_ENDPOINT")
        if "://" not in endpoint:
            endpoint = DEFAULT_S3_ENDPOINT_PROTOCOL + endpoint
        log.info(f"Setting endpoint {endpoint}")
        return cls(
            get_env("AWS_ACCESS_KEY_ID"),
            get_env("AWS_SECRET_ACCESS_KEY"),
            endpoint,
            get_env("AWS_S3_BUCKET"))
