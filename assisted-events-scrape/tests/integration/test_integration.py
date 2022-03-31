from config import ElasticsearchConfig
import elasticsearch
import waiting
import time
import pytest

INIT_DELAY_SECONDS = 10
ALL_EVENTS_NUMBER = 101


class TestIntegration:
    def test_all_docs(self, _wait_for_elastic):
        documents_count = self._es_client.count(index=self._config.index)['count']
        assert(documents_count == ALL_EVENTS_NUMBER)

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
            # As elastic is eventually consistent, we need to make sure we wait more than refresh rate
            time.sleep(INIT_DELAY_SECONDS)
            return True
        return False
