from dataclasses import dataclass
from utils import get_env


DEFAULT_S3_ENDPOINT_PROTOCOL = "s3://"


@dataclass
class ObjectStorageConfig:
    access_key: str
    secret_key: str
    endpoint_url: str
    bucket: str

    @classmethod
    def create_from_env(cls) -> 'ObjectStorageConfig':
        endpoint = get_env("AWS_S3_BUCKET")
        if "://" not in endpoint:
            endpoint = DEFAULT_S3_ENDPOINT_PROTOCOL + endpoint
        return cls(
            get_env("AWS_ACCESS_KEY_ID"),
            get_env("AWS_SECRET_ACCESS_KEY"),
            get_env("AWS_S3_ENDPOINT"),
            get_env("AWS_S3_BUCKET"))
