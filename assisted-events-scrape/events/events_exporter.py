from itertools import chain
import time
import datetime
from typing import Iterable, List
from dateutil import parser
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
        epoch = int(time.time())
        offset = self._offset_repo.load(stream.name)
        log.debug(f"Retrieved offset {offset} for stream {stream.name}")
        checksum = get_dict_hash(offset)

        try:
            docs = self._get_all_docs(stream, offset)
            time_field = stream.options.order_key
            log.debug(f"Retrieved docs (time_field: {time_field}): {docs}")

            def key_fn(document: dict) -> str:
                day = parser.parse(document[time_field])
                day_str = datetime.datetime.strftime(day, "%Y-%m-%d")
                return f"{stream.name}/{day_str}/{epoch}_{checksum}.ndjson"

            offset = self._object_writer.write_ndjson_stream(
                key_fn,
                map(lambda x: x["_source"], docs),
                options=stream.options
            )
            self._offset_repo.save(stream.name, offset)
        except NotFoundError:
            # If run before any event is ever produced there won't be such indices
            pass

    def _get_all_docs(self, stream: EventStream, offsets: DateOffset) -> Iterable[dict]:
        all_docs = []
        partitions = []
        log.debug(f"About to retrieve documents for {stream.name} (offsets: {offsets}, options: {stream.options})")
        if offsets.size() > 0 and stream.options.partition_key:
            log.debug(f"Retrieving documents for partitioned stream {stream.name} (options: {stream.options})")
            for partition, offset in offsets.getAll().items():
                query = self._get_query(stream, partition, offset)
                log.debug(f"Retrieving documents for {stream.name} (partition: {partition}, offset: {offset})")
                docs = helpers.scan(self._es_client, index=stream.name, size=self._config.chunk_size,
                                    query=query, request_timeout=DEFAULT_TIMEOUT)
                all_docs = chain(all_docs, docs)
            partitions = list(offsets.getAll().keys())
        if offsets.size() == 0 and not stream.options.partition_key:
            # When it's the first time we retrieve non-partitioned data
            query = self._get_query(stream, None, None)
            log.debug(f"First time retrieving non-partitioned stream {stream.name} (query: {query})")
            docs = helpers.scan(self._es_client, index=stream.name, size=self._config.chunk_size,
                                query=query, request_timeout=DEFAULT_TIMEOUT)
            all_docs = chain(all_docs, docs)

        # if partitions have been used, retrieve all other partitions that have no offset stored
        if stream.options.partition_key:
            log.debug(f"Make sure all non-present partitions are also retrieved for {stream.name}")
            query = self._get_query_exclude_partitions(stream.options.partition_key, partitions)
            log.debug(f"Retrieving documents for {stream.name}, query: {query}")
            docs = helpers.scan(self._es_client, index=stream.name, size=self._config.chunk_size,
                                query=query, request_timeout=DEFAULT_TIMEOUT)
            all_docs = chain(all_docs, docs)

        return all_docs

    # pylint: disable=no-self-use
    def _get_query(self, stream: EventStream, partition: str, offset: str) -> dict:
        must = []
        if offset:
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

    def _get_query_exclude_partitions(self, partition_key: str, partitions: List[str]) -> dict:
        if not partition_key:
            return {
                "query": {
                    "bool": {
                        "must_not": [
                            {
                                "match_all": {}
                            }
                        ]
                    }
                }
            }
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
    # pylint: enable=no-self-use
