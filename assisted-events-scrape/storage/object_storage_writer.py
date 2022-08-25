from typing import Iterable, Callable
import tempfile
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

    def write_ndjson_stream(self, key_fn: Callable[[dict], str], documents: Iterable[dict],
                            options: DateOffsetOptions = None) -> DateOffset:

        """
        Stream documents to bucket/key.

        :param str key: Key to write documents to
        :param Iterable[str] documents: Documents to be streamed at bucket/key
        """
        offset = None
        if options:
            offset = DateOffset()

        buff = {}
        streams = {}
        for document in documents:
            key = key_fn(document)
            stream = streams.get(key)
            if not stream:
                # pylint: disable=consider-using-with
                buff[key] = tempfile.NamedTemporaryFile(delete=True)
                # pylint: enable=consider-using-with

                transport_params = dict(
                    client=self.client,
                    # 5MB is the minimum part size allowed by AWS S3
                    # We need this number as low as possible, as we will have several multipart upload
                    # in progress when importing large datasets
                    min_part_size=5 * 1024 ** 2,
                    # We also buffer on disk
                    writebuffer=buff[key]
                )

                streams[key] = smart_open.open(
                    f"s3://{self.config.bucket}/{key}",
                    "w",
                    transport_params=transport_params
                )

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
            streams[key].write(document_str + "\n")

        for stream in streams.values():
            stream.close()
        for buff in buff.values():
            buff.close()
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
