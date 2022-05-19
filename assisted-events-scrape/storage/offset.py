from typing import Iterable, List
from dataclasses import dataclass
from dateutil.parser import parse
from opensearchpy import OpenSearch, helpers
from opensearchpy.exceptions import NotFoundError


@dataclass
class DateOffsetOptions:
    partition_key: str
    order_key: str


class DateOffset:
    def __init__(self, items: List[dict] = None):
        self._offsets = {}
        if items:
            for item in items:
                self.setOffset(item.get("offset"), item.get("partition"))

    def setOffset(self, offset: str, partition: str = None):
        """
        When partition is none, it means there is no partition.
        In this case offset will be kept track with `None` key
        """
        if partition in self._offsets:
            if parse(self._offsets[partition]) > parse(offset):
                return None
        self._offsets[partition] = offset

    def getOffset(self, partition: str = None) -> str:
        return self._offsets.get(partition, None)

    def getAll(self) -> dict:
        return self._offsets


class DateOffsetRepository:
    def __init__(self, es_client: OpenSearch, offset_index: str):
        self._es_client = es_client
        self._offset_index = offset_index

    def save(self, stream: str, offsets: DateOffset):
        actions = self._get_actions_from_offsets(stream, offsets)
        return helpers.bulk(self._es_client, actions)

    def load(self, stream: str, partition: str = None) -> DateOffset:
        if partition:
            doc_id = f"{stream}-{partition}"
            resp = self._es_client.get(index=self._offset_index, id=doc_id)
            return DateOffset([resp["_source"]])

        query = {"query": {"bool": {"must": [{"term": {"stream": stream}}]}}}

        try:
            res = self._es_client.search(index=self._offset_index, body=query)
            return DateOffset([item["_source"] for item in res["hits"]["hits"]])
        except NotFoundError:
            # Index not created yet, return empty offset
            return DateOffset()

    def _get_actions_from_offsets(self, stream: str, offsets: DateOffset) -> Iterable[dict]:
        for partition, offset in offsets.getAll().items():
            doc = {
                "stream" : stream,
                "partition": partition,
                "offset": offset
            }
            doc_id = f"{stream}-{partition}"
            yield {
                "_index": self._offset_index,
                "_op_type": "index",
                "_id": doc_id,
                "_source": doc
            }
