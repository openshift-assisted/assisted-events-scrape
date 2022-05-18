from storage import ObjectStorageWriter
from config import ObjectStorageConfig
from unittest.mock import Mock


class TestObjectStorageWriter:
    def setup(self):
        cfg = ObjectStorageConfig(
            "mykey",
            "mysecret",
            "myendpoint",
            "mybucket"
        )
        self._client = Mock()
        self._writer = ObjectStorageWriter(
            self._client,
            cfg
        )

    def test_get_offset(self):
        doc = {
            "foo": 123,
            "bar": {
                "foobar": 456
            }
        }
        offset = self._writer._get_offset_from_doc(doc, "foo")
        assert offset == 123

        offset = self._writer._get_offset_from_doc(doc, "bar.foobar")
        assert offset == 456

        offset = self._writer._get_offset_from_doc(doc, "this.key.is.undefined")

        assert offset is None

        offset = self._writer._get_offset_from_doc(doc, "")
        assert offset is None
