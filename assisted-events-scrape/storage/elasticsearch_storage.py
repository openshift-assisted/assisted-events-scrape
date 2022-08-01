from typing import List, Callable, Iterable
from clients import create_es_client_from_env
from utils import log
from opensearchpy import OpenSearch, helpers
from opensearchpy.exceptions import NotFoundError, ConnectionTimeout, TransportError
from retry import retry
from sentry_sdk import capture_exception

DEFAULT_SCAN_SIZE = 500
DEFAULT_SCROLL_WINDOW = '5m'


class ElasticsearchStorage:
    """
    This class is used to store documents in Elasticsearch.
    """
    @classmethod
    def create_from_env(cls) -> 'ElasticsearchStorage':
        es_client = create_es_client_from_env()
        return cls(es_client)

    def __init__(self, es_client: OpenSearch):
        self._es_client = es_client

    def store_changes(self, index: str, documents: List[dict], id_fn: Callable[[dict], str],
                      transform_document_fn: Callable[[dict], dict] = None, filter_by: dict = None):
        """
        Stores documents that are not already stored, by retrieving what is stored first.
        It is very important to filter by a reasonable key for performance purposes: if we won't
        filter, we will be scanning through the whole corpus of document, impacting time and memory
        consumption.

        :param str index: Index to store documents in
        :param List[dict] documents: List of documents to be stored
        :param Callable[[dict], str] id_fn: Function to extract the ID from each document. Document is input,
        and the output should be a string
        :param Callable[[dict], dict] transform_document_fn: Function to transform document. Useful to add/remove fields
        :param dict filter_by: Filter document when scanning. This is useful for performance
        """
        actions = self._get_new_documents_actions(
            index=index,
            documents=documents,
            id_fn=id_fn,
            transform_document_fn=transform_document_fn,
            filter_by=filter_by)
        self._bulk(actions)

    @retry((TransportError, ConnectionTimeout), delay=1, tries=3, backoff=2, max_delay=4, jitter=1)
    def _bulk(self, actions):
        try:
            helpers.bulk(self._es_client, actions)
        except helpers.BulkIndexError as e:
            capture_exception(e)
            log.exception("captured exception while bulk index")

    def _get_new_documents_actions(self, index: str, documents: List[dict],
                                   id_fn: Callable[[dict], str], transform_document_fn: Callable[[dict], dict],
                                   filter_by: dict) -> Iterable[dict]:
        """
        Returns actions compatible with bulk payload for input documents that are not already stored.

        :param str index: Index to store documents in
        :param List[dict] documents: List of documents to be stored
        :param Callable[[dict], str] id_fn: Function to extract the ID from each document. Document is input,
        and the output should be a string
        :param Callable[[dict], dict] transform_document_fn: Function to transform document. Useful to add custom fields
        :param dict filter_by: Filter document when scanning. This is useful for performance

        :return Generator containing elasticsearch bulk actions.
        :rtype Iterable[dict]
        """
        def identity(x: dict) -> dict:
            return x

        all_ids = set()
        if filter_by is None:
            filter_by = {"match_all": {}}

        query = {
            "query": filter_by,
            "_source": [""]
        }

        existing_docs = []
        try:
            existing_docs = self._scan(index=index, query=query)
        except helpers.ScanError as e:
            capture_exception(e)
            log.exception("captured exception while scanning")

        if transform_document_fn is None:
            transform_document_fn = identity

        try:
            for d in existing_docs:
                all_ids.add(d["_id"])
        except NotFoundError:
            # first time we set documents index will be not found
            # In this case, there are no existing documents
            pass

        for d in documents:
            doc_id = id_fn(d)
            if doc_id not in all_ids:
                yield {
                    "_index": index,
                    "_id": doc_id,
                    "_source": transform_document_fn(d),
                    "_op_type": "index"
                }

    @retry((TransportError, ConnectionTimeout), delay=1, tries=3, backoff=2, max_delay=4, jitter=1)
    def _scan(self, index, query):
        return helpers.scan(self._es_client, index=index, query=query)
