from dataclasses import dataclass
from utils import get_env


@dataclass
class ObjectStorageConfig:
    access_key: str
    secret_key: str
    endpoint_url: str
    bucket: str

    @classmethod
    def create_from_env(cls) -> 'ObjectStorageConfig':
        return cls(
            get_env("AWS_ACCESS_KEY_ID"),
            get_env("AWS_SECRET_ACCESS_KEY"),
            get_env("AWS_S3_ENDPOINT"),
            get_env("AWS_S3_BUCKET"))
