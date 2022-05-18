import re
import os
from events import EventsExporter, EventStream
from config import EventExportConfig
from clients import create_es_client_from_env
from storage import ObjectStorageWriter, DateOffsetRepository, DateOffsetOptions, ElasticsearchStorage
import boto3
import pytest


class TestEventsExporter:
    def setup(self):
        self._offset_index = "test-offsets"
        self._events_index = "test-myevents"
        self._es_client = create_es_client_from_env()
        self._config = EventExportConfig(100)
        self._writer = ObjectStorageWriter.create_from_env()
        self._offset_repo = DateOffsetRepository(self._es_client, self._offset_index)
        self._es_store = ElasticsearchStorage(self._es_client)

        self._exporter = EventsExporter(
            self._config,
            self._es_client,
            self._writer,
            self._offset_repo
        )
        endpoint_url = os.getenv("AWS_S3_ENDPOINT")
        session = boto3.Session(
            aws_access_key_id="myaccesskey",
            aws_secret_access_key="mysecretkey"
        )
        self._s3_client = session.client('s3', endpoint_url=f"{endpoint_url}")
        self._stream = EventStream(
            self._events_index,
            DateOffsetOptions(
                "partition",
                "timestamp"
            )
        )

    def teardown(self):
        self._delete_s3_objects()
        self._es_client.indices.delete(index=self._events_index, ignore=[400, 404])
        self._es_client.indices.delete(index=self._offset_index, ignore=[400, 404])

    def test_export(self, _batches):
        batch_lines_count = []
        for i, batch in enumerate(_batches):
            batch_lines_count.append(len(batch))
            self._es_store.store_changes(
                self._events_index,
                documents=batch,
                id_fn=lambda x: x["id"]
            )

            # Sync events index
            self._es_client.indices.refresh(index=self._events_index)

            self._exporter.export_stream(self._stream)

            # Sync offset index
            self._es_client.indices.refresh(index=self._offset_index)

            objects = self._get_s3_objects()

            assert len(objects) == (i + 1)

        for obj in objects:
            body = self._get_s3_object_body(obj['Key'])
            lines = body.rstrip().split("\n")
            count = len(lines)
            # make sure there is one item with such lines, and remove it
            assert count in batch_lines_count
            batch_lines_count.remove(count)

    @pytest.fixture
    def _batches(self):
        yield [
            [
                {"id": 1, "timestamp": "2022-01-01T00:00:00", "partition": "A"},
                {"id": 2, "timestamp": "2022-01-01T00:00:01", "partition": "A"},
                {"id": 3, "timestamp": "2022-01-01T00:00:02", "partition": "B"},
                {"id": 4, "timestamp": "2022-01-01T00:00:03", "partition": "C"},
                {"id": 5, "timestamp": "2022-01-01T00:00:04", "partition": "C"},
                {"id": 6, "timestamp": "2022-01-01T00:00:05", "partition": "B"},
                {"id": 7, "timestamp": "2022-01-01T00:00:06", "partition": "A"},
            ],
            [
                {"id": 8, "timestamp": "2022-01-01T00:00:10", "partition": "A"},
                {"id": 9, "timestamp": "2022-01-01T00:00:20", "partition": "A"},
                {"id": 10, "timestamp": "2022-01-01T00:00:30", "partition": "B"},
                {"id": 11, "timestamp": "2022-01-01T00:00:40", "partition": "C"},
                {"id": 12, "timestamp": "2022-01-01T00:00:50", "partition": "C"},
                {"id": 13, "timestamp": "2022-01-01T00:01:00", "partition": "B"},
                {"id": 14, "timestamp": "2022-01-01T00:01:10", "partition": "A"},
                {"id": 15, "timestamp": "2022-01-01T00:01:20", "partition": "A"},
            ]
        ]

    def _get_s3_object_body(self, key: str):
        resp = self._s3_client.get_object(Bucket='mybucket', Key=key)
        return resp['Body'].read().decode('utf-8')

    def _delete_s3_objects(self):
        objects = self._get_s3_objects()
        for obj in objects:
            if obj:
                self._s3_client.delete_object(Bucket='mybucket', Key=obj['Key'])

    def _get_s3_objects(self):
        result = []
        objects = self._s3_client.list_objects(Bucket='mybucket')
        for obj in objects['Contents']:
            match = re.search('export-[0-9]{4}-[0-9]{2}-[0-9]{2}/' + self._events_index + '_.*.ndjson', obj['Key'])
            if match:
                result.append(obj)
        return sorted(result, key=_get_last_modified)


def _get_last_modified(obj: dict):
    return int(obj['LastModified'].strftime('%s'))
