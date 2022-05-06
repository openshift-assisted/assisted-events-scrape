from storage import DateOffset


class TestDateOffset:
    def setup(self):
        self._offset = DateOffset()

    def test_offset(self):
        self._offset.setOffset("2022-01-01")
        self._offset.setOffset("2021-01-01")

        offset = self._offset.getOffset()
        assert offset == "2022-01-01"

    def test_offset_with_partition(self):
        self._offset.setOffset("2022-01-01", "A")
        self._offset.setOffset("2021-01-01", "A")

        self._offset.setOffset("2023-02-01", "B")
        self._offset.setOffset("2022-02-01", "B")
        self._offset.setOffset("2024-02-01", "B")

        offset = self._offset.getOffset("A")
        assert offset == "2022-01-01"

        offset = self._offset.getOffset("B")
        assert offset == "2024-02-01"
