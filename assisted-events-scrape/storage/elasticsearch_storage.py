from typing import List, Callable, Iterable
from utils import log
from config import ElasticsearchConfig
from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import NotFoundError

DEFAULT_SCAN_SIZE = 500
DEFAULT_SCROLL_WINDOW = '5m'


class ElasticsearchStorage:
    """
    This class is used to store documents in Elasticsearch.
    """
    @classmethod
    def create(cls) -> 'ElasticsearchStorage':
        config = ElasticsearchConfig.create_from_env()
        http_auth = None
        if config.username:
            http_auth = (config.username, config.password)
        es_client = Elasticsearch(config.host, http_auth=http_auth)
        return cls(es_client)

    def __init__(self, es_client: Elasticsearch):
        self._es_client = es_client

    def store_changes(self, index: str, documents: List[dict], id_fn: Callable[[dict], str], filter_by: dict = None):
        """
        Stores documents that are not already stored, by retrieving what is stored first.
        It is very important to filter by a reasonable key for performance purposes: if we won't
        filter, we will be scanning through the whole corpus of document, impacting time and memory
        consumption.

        :param str index: Index to store documents in
        :param List[dict] documents: List of documents to be stored
        :param Callable[[dict], str]: Function to extract the ID from each document. Document is input,
        and the output should be a string
        :param dict filter_by: Filter document when scanning. This is useful for performance
        """
        actions = self._get_new_documents_actions(
            index=index,
            documents=documents,
            id_fn=id_fn,
            filter_by=filter_by)
        return helpers.bulk(self._es_client, actions)

    def _get_new_documents_actions(self, index: str, documents: List[dict],
                                   id_fn: Callable[[dict], str], filter_by: dict) -> Iterable[dict]:
        """
        Returns actions compatible with bulk payload for input documents that are not already stored.

        :param str index: Index to store documents in
        :param List[dict] documents: List of documents to be stored
        :param Callable[[dict], str]: Function to extract the ID from each document. Document is input,
        and the output should be a string
        :param dict filter_by: Filter document when scanning. This is useful for performance

        :return Generator containing elasticsearch bulk actions.
        :rtype Iterable[dict]
        """
        all_ids = set()
        existing_docs = self.scan(index=index, filter_by=filter_by)

        for d in existing_docs:
            all_ids.add(d["_id"])
        for d in documents:
            doc_id = id_fn(d)
            if doc_id not in all_ids:
                yield {
                    "_index": index,
                    "_id": doc_id,
                    "_source": d,
                    "_op_type": "index"
                }

    def scan(self, index: str, filter_by: dict = None, source: list = None,
             scroll: str = DEFAULT_SCROLL_WINDOW, size: int = DEFAULT_SCAN_SIZE) -> Iterable[dict]:
        """
        Reimplementation of scan method, as the one coming with the library does not accept `_source`
        as parameter and it was needed.

        :param str index: Index to store documents in
        :param dict filter_by: Filter document when scanning.
        :param list source: List of fields to be returned. Defaults to empty (only metadata, like _id)
        :param scroll str: Scrolling time. Defaults to 5m
        :param size int: Scrolling size. Defaults to 500

        :return Generator of documents that match scanning criteria
        :rtype Iterable[dict]
        """
        body = {"query": {"match_all": {}}}
        if filter_by is not None:
            body = {"query": {"term": filter_by}}

        if source is None:
            source = [""]

        hits = []

        try:
            docs = self._es_client.search(
                index=index,
                body=body,
                scroll=scroll,
                size=size,
                _source=source
            )
            hits = docs["hits"]["hits"]
            scroll_id = docs["_scroll_id"]
            yield from hits
        except NotFoundError:
            log.warning(f"Could not scan index {index}: not found")

        while len(hits) > 0:
            docs = self._es_client.scroll(scroll_id=scroll_id, scroll=scroll)
            scroll_id = docs["_scroll_id"]
            hits = docs["hits"]["hits"]
            yield from hits
