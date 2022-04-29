from config import ElasticsearchConfig
import elasticsearch
import hashlib
import json
from storage import ElasticsearchStorage


class TestElasticsearchStorage:
    def setup(self):
        config = ElasticsearchConfig.create_from_env()
        self._es_client = elasticsearch.Elasticsearch(config.host)
        self._es_store = ElasticsearchStorage(self._es_client)
        self._index = "testindex"

    def teardown(self):
        self._es_client.indices.delete(index=self._index, ignore=[400, 404])
        self._es_store = None
        self._es_client = None

    def test_store_changes(self):
        d = {"foo": "bar"}
        docs = [d]
        self._es_store.store_changes(
            index=self._index,
            documents=docs,
            id_fn=get_doc_id)
        d = {"foobar": "barfoo"}
        docs.append(d)
        self._es_store.store_changes(
            index=self._index,
            documents=docs,
            id_fn=get_doc_id)

        # make sure the value is visible in the index
        self._es_client.indices.refresh(index=self._index)

        all_docs = self._es_client.search(index=self._index)

        assert len(all_docs["hits"]["hits"]) == 2

        # Insert again the same records, should not store anything new
        self._es_store.store_changes(
            index=self._index,
            documents=docs,
            id_fn=get_doc_checksum)

        assert len(all_docs["hits"]["hits"]) == 2

    def test_store_changes_checksum(self):
        docs = [{
            "foo": "bar",
        }]
        self._es_store.store_changes(
            index=self._index,
            documents=docs,
            id_fn=get_doc_checksum)
        docs.append({"foo": "bar", "timestamp": "2021-03-01T00:00:00.000Z"})
        self._es_store.store_changes(
            index=self._index,
            documents=docs,
            id_fn=get_doc_checksum)

        # make sure the value is visible in the index
        self._es_client.indices.refresh(index=self._index)

        all_docs = self._es_client.search(index=self._index)

        assert len(all_docs["hits"]["hits"]) == 1

    def test_store_changes_filtered(self):
        filter_by = {"cluster_id": "da932361-df0a-4bfa-8b4f-599bb2db5135"}
        docs = [{
            "cluster_id": "da932361-df0a-4bfa-8b4f-599bb2db5135",
            "foo": "bar",
        }]
        self._es_store.store_changes(
            index=self._index,
            documents=docs,
            id_fn=get_doc_checksum,
            filter_by=filter_by
        )
        docs.append({
            "foo": "bar",
            "cluster_id": "da932361-df0a-4bfa-8b4f-599bb2db5135",
            "timestamp": "2021-03-01T00:00:00.000Z"
        })
        self._es_store.store_changes(
            index=self._index,
            documents=docs,
            id_fn=get_doc_checksum,
            filter_by=filter_by
        )

        # make sure the value is visible in the index
        self._es_client.indices.refresh(index=self._index)

        all_docs = self._es_client.search(index=self._index)

        assert len(all_docs["hits"]["hits"]) == 1

    def test_scan(self):
        doc = {"foo": "bar"}
        self._es_client.index(self._index, doc, refresh=True)

        docs = self._es_store.scan(self._index)

        assert len(list(docs)) == 1

        self._es_client.index(self._index, {"barfoo": "bar"}, refresh=True)
        self._es_client.index(self._index, {"qux": "bar"}, refresh=True)

        # test that paging works
        docs = self._es_store.scan(self._index, size=1)

        assert len(list(docs)) == 3

    def test_scan_with_filter(self):
        # default mapping will create .keyword property for filtering
        filter_by = {"foo.keyword": "bar"}
        doc = {"foo": "bar"}
        self._es_client.index(self._index, doc, refresh=True)

        docs = self._es_store.scan(index=self._index, filter_by=filter_by)

        assert len(list(docs)) == 1

        self._es_client.index(self._index, {"barfoo": "bar"}, refresh=True)
        self._es_client.index(self._index, {"qux": "bar"}, refresh=True)

        docs = self._es_store.scan(self._index, size=1, filter_by=filter_by)

        # it should filter out previously inserted records
        assert len(list(docs)) == 1

        self._es_client.index(self._index, {"foo": "bar", "foobar": "qux"}, refresh=True)
        self._es_client.index(self._index, {"qux": "barfoo", "foo": "bar"}, refresh=True)

        # page and filter
        docs = self._es_store.scan(self._index, size=1, filter_by=filter_by)

        assert len(list(docs)) == 3

    def test_scan_source(self):
        filter_by = {"foo.keyword": "bar"}
        doc = {"foo": "bar"}
        self._es_client.index(self._index, doc, refresh=True)

        docs = self._es_store.scan(index=self._index, filter_by=filter_by)

        assert len(list(docs)) == 1
        # default source should not be populated
        for doc in docs:
            assert "foo" not in doc["_source"]

        # retrieve foo field
        docs = self._es_store.scan(index=self._index, filter_by=filter_by, source=["foo"])

        # default source should not be populated
        for doc in docs:
            assert "foo" in doc["_source"]

    def test_scan_undefined_index(self):
        docs = self._es_store.scan(index="undefined")
        assert 0 == len(list(docs))


def get_doc_id(doc: dict) -> str:
    return hashlib.sha256(json.dumps(doc).encode('utf-8')).hexdigest()


def get_doc_checksum(doc: dict) -> str:
    payload = doc
    if "timestamp" in doc:
        del payload["timestamp"]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()
