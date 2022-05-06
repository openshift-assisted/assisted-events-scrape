import os
import json
import boto3
from storage import ObjectStorageWriter


class TestObjectStorage:
    def setup(self):
        self._writer = ObjectStorageWriter.create_from_env()
        endpoint_url = os.getenv("AWS_S3_ENDPOINT")
        session = boto3.Session(
            aws_access_key_id="myaccesskey",
            aws_secret_access_key="mysecretkey"
        )
        self._s3_client = session.client('s3', endpoint_url=f"{endpoint_url}")

    def test_write_stream(self):
        random_items = self._random_items()
        self._writer.write_ndjson_stream("foobar/barfoo.ndjson", random_items, )
        resp = self._s3_client.get_object(Bucket='mybucket', Key="foobar/barfoo.ndjson")

        assert resp['ResponseMetadata']['HTTPStatusCode'] == 200
        obj_str = resp['Body'].read().decode('utf-8')
        objects = []
        for line in obj_str.rstrip().split('\n'):
            objects.append(json.loads(line))

        assert objects == list(self._random_items())

        self._s3_client.delete_object(Bucket='mybucket', Key="foobar/barfoo.ndjson")

    def _random_items(self):
        items = [
            {"foo": "bar"},
            {"bar": "foo"},
            {"foobar": "qux"},
            {"abc": "def"}
        ]
        for item in items:
            yield item
