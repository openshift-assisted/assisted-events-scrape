from typing import Iterable
import json
import boto3
import smart_open
import dpath.util
from utils import log
from config import ObjectStorageConfig
from .offset import DateOffsetOptions, DateOffset


class ObjectStorageWriter:
    """
    Writes documents to object storage
    """
    @classmethod
    def create(cls, client, config: ObjectStorageConfig) -> 'ObjectStorageWriter':
        return cls(client, config)

    @classmethod
    def create_from_env(cls) -> 'ObjectStorageWriter':
        config = ObjectStorageConfig.create_from_env()
        session = boto3.Session(
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key
        )
        client = session.client('s3', endpoint_url=config.endpoint_url)
        return cls(client, config)

    def __init__(self, client, config: ObjectStorageConfig):
        self.config = config
        self.client = client

    def write_ndjson_stream(self, key: str, documents: Iterable[dict], options: DateOffsetOptions = None) -> DateOffset:

        """
        Stream documents to bucket/key.

        :param str key: Key to write documents to
        :param Iterable[str] documents: Documents to be streamed at bucket/key
        """
        offset = None
        if options:
            offset = DateOffset()

        with smart_open.open(
                f"s3://{self.config.bucket}/{key}",
                "w",
                transport_params=dict(client=self.client)) as bucket:

            for document in documents:
                if options:
                    doc_offset = None
                    partition = None
                    if options.order_key:
                        doc_offset = self._get_offset_from_doc(document, options.order_key)
                    if options.partition_key:
                        partition = self._get_partition_from_doc(document, options.partition_key)
                    offset.setOffset(doc_offset, partition)
                log.debug(f"Writing document: {document}")
                document_str = json.dumps(document)
                bucket.write(document_str + "\n")
        return offset

    # pylint: disable=no-self-use
    def _get_partition_from_doc(self, doc: dict, partition_key: str) -> str:
        try:
            return dpath.util.get(doc, partition_key, separator=".")
        except KeyError:
            return None

    def _get_offset_from_doc(self, doc: dict, order_key: str) -> str:
        try:
            return dpath.util.get(doc, order_key, separator=".")
        except KeyError:
            return None
    # pylint: enable=no-self-use
