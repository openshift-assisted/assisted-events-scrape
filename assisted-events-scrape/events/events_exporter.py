from datetime import date
import time
from itertools import chain
from typing import Iterable, List
from config import EventExportConfig
from utils import get_dict_hash, log
from events import EventStream
from storage import DateOffset, DateOffsetRepository, ObjectStorageWriter
from opensearchpy.exceptions import NotFoundError
from opensearchpy import OpenSearch, helpers


DEFAULT_TIMEOUT = 30.0


class EventsExporter:
    def __init__(self, config: EventExportConfig, es_client: OpenSearch,
                 object_writer: ObjectStorageWriter, offset_repo: DateOffsetRepository):
        self._config = config
        self._es_client = es_client
        self._object_writer = object_writer
        self._offset_repo = offset_repo

    def export_stream(self, stream: EventStream):
        today_str = date.today().strftime("%Y-%m-%d")
        epoch = int(time.time())
        offset = self._offset_repo.load(stream.name)
        log.debug(f"Retrieved offset {offset} for stream {stream.name}")
        checksum = get_dict_hash(offset)

        try:
            docs = self._get_all_docs(stream, offset)
            key = f"export-{today_str}/{stream.name}_{epoch}_{checksum}.ndjson"
            offset = self._object_writer.write_ndjson_stream(
                key,
                map(lambda x: x["_source"], docs),
                options=stream.options
            )
            self._offset_repo.save(stream.name, offset)
        except NotFoundError:
            # If run before any event is ever produced there won't be such indices
            pass

    def _get_all_docs(self, stream: EventStream, offsets: DateOffset) -> Iterable[dict]:
        all_docs = []
        if offsets:
            for partition, offset in offsets.getAll().items():
                query = _get_query(stream, partition, offset)
                log.debug(f"Retrieving documents for {stream.name}, query: {query}")
                docs = helpers.scan(self._es_client, index=stream.name, size=self._config.chunk_size,
                                    query=query, request_timeout=DEFAULT_TIMEOUT)
                all_docs = chain(all_docs, docs)
            partitions = list(offsets.getAll().keys())
        query = _get_query_exclude_partitions(stream.options.partition_key, partitions)
        log.debug(f"Retrieving documents for {stream.name}, query: {query}")
        docs = helpers.scan(self._es_client, index=stream.name, size=self._config.chunk_size,
                            query=query, request_timeout=DEFAULT_TIMEOUT)
        return chain(all_docs, docs)


def _get_query(stream: EventStream, partition: str, offset: str) -> dict:
    offset_range = {"range": {stream.options.order_key: {"gt": offset}}}
    must = [offset_range]

    if stream.options.partition_key:
        partition_filter = {"term": {stream.options.partition_key: partition}}
        must.append(partition_filter)

    return {
        "query": {
            "bool": {
                "must": must
            }
        }
    }


def _get_query_exclude_partitions(partition_key: str, partitions: List[str]) -> dict:
    return {
        "query": {
            "bool": {
                "must_not": [
                    {
                        "terms": {
                            partition_key: partitions
                        }
                    }
                ]
            }
        }
    }
