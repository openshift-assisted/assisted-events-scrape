from config import ElasticsearchConfig
import elasticsearch
import waiting
from waiting import TimeoutExpired
import pytest

ALL_EVENTS_NUMBER = 101
ASSERTION_TIMEOUT_SECONDS = 2
ASSERTION_WAIT_SECONDS = 1


class TestIntegration:
    def test_all_docs(self, _wait_for_elastic):
        expected_count_idx = {
            self._config.index: ALL_EVENTS_NUMBER,
            ".events": ALL_EVENTS_NUMBER,
        }

        # As elasticsearch is eventually consistent, make sure data is synced
        self._es_client.indices.refresh(index=self._config.index)

        def check_document_count(index, expected_count):
            documents_count = self._es_client.count(index=index)['count']
            return documents_count == expected_count

        for index, expected_count in expected_count_idx.items():
            try:
                waiting.wait(
                    lambda: check_document_count(index, expected_count),
                    timeout_seconds=ASSERTION_TIMEOUT_SECONDS,
                    sleep_seconds=ASSERTION_WAIT_SECONDS,
                    waiting_for="document count"
                )
                # Wait function succeeded, it means doc count was checked within
                assert True
            except TimeoutExpired:
                # Wait function expired, it means doc count could not match in the given time
                assert False

    @pytest.fixture
    def _wait_for_elastic(self):
        self._config = ElasticsearchConfig.create_from_env()
        self._es_client = elasticsearch.Elasticsearch(self._config.host)
        waiting.wait(
            self._is_elastic_ready,
            timeout_seconds=300,
            sleep_seconds=5,
            waiting_for="elasticsearch to become ready",
            expected_exceptions=Exception,
        )

    def _is_elastic_ready(self) -> bool:
        is_elastic_ready = self._es_client.indices.exists(index=self._config.index)
        if is_elastic_ready:
            return True
        return False
