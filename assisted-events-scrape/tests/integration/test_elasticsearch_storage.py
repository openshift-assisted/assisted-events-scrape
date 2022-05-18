from config import ElasticsearchConfig
import opensearchpy
import hashlib
import json
from storage import ElasticsearchStorage


class TestElasticsearchStorage:
    def setup(self):
        config = ElasticsearchConfig.create_from_env()
        self._es_client = opensearchpy.OpenSearch(config.host)
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

    def test_store_changes_with_id_fn(self):
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

    def test_store_changes_with_enrich_document_fn(self):
        def add_qux(x: dict) -> dict:
            x["qux"] = "foobar"
            return x

        docs = [{
            "foo": "bar",
        }]
        self._es_store.store_changes(
            index=self._index,
            documents=docs,
            id_fn=get_doc_checksum,
            enrich_document_fn=add_qux
        )

        # make sure the value is visible in the index
        self._es_client.indices.refresh(index=self._index)

        all_docs = self._es_client.search(index=self._index)

        assert len(all_docs["hits"]["hits"]) == 1
        assert "qux" in all_docs["hits"]["hits"][0]["_source"]
        assert all_docs["hits"]["hits"][0]["_source"]["qux"] == "foobar"

        # still won't add a new document if we try without enrich document fn
        self._es_store.store_changes(
            index=self._index,
            documents=docs,
            id_fn=get_doc_checksum
        )
        all_docs = self._es_client.search(index=self._index)
        assert len(all_docs["hits"]["hits"]) == 1

    def test_store_changes_filtered(self):
        filter_by = {"term": {"cluster_id": "da932361-df0a-4bfa-8b4f-599bb2db5135"}}
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


def get_doc_id(doc: dict) -> str:
    return hashlib.sha256(json.dumps(doc).encode('utf-8')).hexdigest()


def get_doc_checksum(doc: dict) -> str:
    payload = doc
    if "timestamp" in doc:
        del payload["timestamp"]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()
