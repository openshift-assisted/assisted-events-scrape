from clients import create_es_client_from_env
from storage import DateOffset, DateOffsetRepository


class TestDateOffset:
    def setup(self):
        self._index = "test-offsets"
        self._es_client = create_es_client_from_env()
        self._offset_repo = DateOffsetRepository(
            self._es_client,
            self._index
        )

    def teardown(self):
        self._es_client.indices.delete(index=self._index, ignore=[400, 404])

    def test_save_and_load(self):
        offset = DateOffset()
        offset.setOffset("2000-01-01")

        self._offset_repo.save("mystream", offset)

        # Make sure we sync indices
        self._es_client.indices.refresh(index=self._index)

        loaded_offset = self._offset_repo.load("mystream")
        assert loaded_offset.getOffset() == "2000-01-01"

        offset = DateOffset([
            {"offset": "2000-01-01", "partition": "A"},
            {"offset": "2001-01-01", "partition": "B"},
        ])

        self._offset_repo.save("mystream", offset)

        # Make sure we sync indices
        self._es_client.indices.refresh(index=self._index)

        loaded_offset = self._offset_repo.load("mystream")

        assert loaded_offset.getOffset("A") == "2000-01-01"
        assert loaded_offset.getOffset("B") == "2001-01-01"

        # test overriding A leaves B intact
        offset = DateOffset([{"offset": "2000-02-01", "partition": "A"}])

        self._offset_repo.save("mystream", offset)

        # Make sure we sync indices
        self._es_client.indices.refresh(index=self._index)

        loaded_offset = self._offset_repo.load("mystream")
        assert loaded_offset.getOffset("A") == "2000-02-01"
        assert loaded_offset.getOffset("B") == "2001-01-01"
