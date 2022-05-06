from config import ElasticsearchConfig
import elasticsearch
import waiting
import boto3
import os
import re
from typing import List
from config import EventStoreConfig
from waiting import TimeoutExpired
from utils import log
import pytest

ALL_EVENTS_NUMBER = 101
ALL_CLUSTERS_NUMBER = 2
ALL_VERSIONS_NUMBER = 1
ASSERTION_TIMEOUT_SECONDS = 2
ASSERTION_WAIT_SECONDS = 1


class TestIntegration:
    def test_event_scrape(self, _wait_for_elastic):
        expected_count_idx = {
            self._config.index: ALL_EVENTS_NUMBER,
            EventStoreConfig.EVENTS_INDEX: ALL_EVENTS_NUMBER,
            EventStoreConfig.CLUSTER_EVENTS_INDEX: ALL_CLUSTERS_NUMBER,
            EventStoreConfig.COMPONENT_VERSIONS_EVENTS_INDEX: ALL_VERSIONS_NUMBER,
        }

        # As elasticsearch is eventually consistent, make sure data is synced
        self._es_client.indices.refresh(index=self._config.index)

        def check_document_count(index, expected_count):
            documents_count = self._es_client.count(index=index)['count']
            if documents_count != expected_count:
                log.warning(f"Index {index}: found {documents_count} documents, expected {expected_count}")
                return False
            return True

        for index, expected_count in expected_count_idx.items():
            try:
                waiting.wait(
                    lambda: check_document_count(index, expected_count),
                    timeout_seconds=ASSERTION_TIMEOUT_SECONDS,
                    sleep_seconds=ASSERTION_WAIT_SECONDS,
                    waiting_for=f"{index} document count to be {expected_count}"
                )
                # Wait function succeeded, it means doc count was checked within
                assert True
            except TimeoutExpired:
                # Wait function expired, it means doc count could not match in the given time
                assert False

    def test_s3_upload(self):
        endpoint_url = os.getenv("AWS_S3_ENDPOINT")
        session = boto3.Session(
            aws_access_key_id="myaccesskey",
            aws_secret_access_key="mysecretkey"
        )
        client = session.client('s3', endpoint_url=f"{endpoint_url}")
        objects = client.list_objects(Bucket='mybucket')
        # it shoul have one each event type
        assert len(objects['Contents']) == 3
        assert at_least_one_matches_key(objects['Contents'], "Key", ".*events.*")
        assert at_least_one_matches_key(objects['Contents'], "Key", ".*clusters.*")
        assert at_least_one_matches_key(objects['Contents'], "Key", ".*component_versions.*")

        # Clean up
        for obj in objects['Contents']:
            client.delete_object(Bucket='mybucket', Key=obj['Key'])

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


def at_least_one_matches_key(objects: List[dict], key: str, match: str) -> bool:
    for obj in objects:
        if key not in obj:
            continue
        if re.search(match, obj[key]):
            return True
    return False
