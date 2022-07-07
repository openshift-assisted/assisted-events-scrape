from events import EventsExporter, EventStream
from storage import DateOffsetOptions
from unittest.mock import Mock


class TestEventsExporter:
    def setup(self):
        self._exporter = EventsExporter(Mock(), Mock(), Mock(), Mock())

    def test_query(self):
        stream = EventStream(
            "foobar",
            DateOffsetOptions(
                "mypartitionkey",
                "mytimestamp"
            )
        )
        query = self._exporter._get_query(
            stream,
            "mypartition",
            "2022-01-01"
        )
        expected_query = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"mytimestamp": {"gt": "2022-01-01"}}},
                        {"term": {"mypartitionkey": "mypartition"}}
                    ]
                }
            }
        }
        assert query == expected_query

        query = self._exporter._get_query_exclude_partitions(
            "mypartitionkey",
            ["foo", "bar", "qux"]
        )
        expected_query = {
            "query": {
                "bool": {
                    "must_not": [
                        {
                            "terms": {
                                "mypartitionkey": ["foo", "bar", "qux"]
                            }
                        }
                    ]
                }
            }
        }
        assert query == expected_query

    def test_query_no_partition(self):
        stream = EventStream(
            "foobar",
            DateOffsetOptions(
                None,
                "mytimestamp"
            )
        )
        query = self._exporter._get_query(
            stream,
            None,
            "2022-02-02"
        )
        expected_query = {
            "query": {
                "bool": {
                    "must": [
                        {"range": {"mytimestamp": {"gt": "2022-02-02"}}}
                    ]
                }
            }
        }
        assert query == expected_query

        query = self._exporter._get_query_exclude_partitions(
            None,
            []
        )
        expected_query = {
            "query": {
                "bool": {
                    "must_not": [
                        {
                            "match_all": {}
                        }
                    ]
                }
            }
        }
        assert query == expected_query
