import logging
from queue import Queue
from unittest.mock import Mock
from workers.cluster_events_worker import ClusterEventsWorker
from utils.counters import ErrorCounter
from utils.counters import Changes


class TestClusterEventsWorker():
    def setup(self):
        logging.disable(logging.CRITICAL)
        self.queue = Queue()
        self.cluster_repo_mock = Mock()
        self.event_repo_mock = Mock()
        self.cluster_events_storage_mock = Mock()
        self.error_counter = ErrorCounter()
        self.changes = Changes()
        config = {
            "name": "Test-Worker",
            "queue": self.queue,
            "error_counter": self.error_counter,
            "changes": self.changes
        }
        self.worker = ClusterEventsWorker(
            config,
            self.cluster_repo_mock,
            self.event_repo_mock,
            self.cluster_events_storage_mock)

    def teardown(self):
        self.worker = None

    def test_error_getting_cluster(self):
        self.cluster_repo_mock.get_cluster_hosts.side_effect = Exception("Error getting cluster's hosts")

        cluster = {"id": "abcd", "name": "mycluster"}
        self.worker.store_events_for_cluster(cluster)
        self.event_repo_mock.get_cluster_events.assert_not_called()
        self.cluster_events_storage_mock.store.assert_not_called()

        assert 1 == self.error_counter.get_errors()
        assert not self.changes.has_changed_in_last_minutes(1)

    def test_error_getting_events(self):
        self.event_repo_mock.get_cluster_events.side_effect = Exception("Error getting cluster")

        cluster = {"id": "abcd", "name": "mycluster"}
        self.worker.store_events_for_cluster(cluster)
        self.cluster_repo_mock.get_cluster_hosts.assert_called_once()
        self.cluster_events_storage_mock.store.assert_not_called()

        assert 1 == self.error_counter.get_errors()
        assert not self.changes.has_changed_in_last_minutes(1)

    def test_error_storing_events(self):
        self.cluster_events_storage_mock.store.side_effect = Exception("Error getting cluster")

        cluster = {"id": "abcd", "name": "mycluster"}
        self.worker.store_events_for_cluster(cluster)
        self.cluster_repo_mock.get_cluster_hosts.assert_called_once()
        self.event_repo_mock.get_cluster_events.assert_called_once()

        assert 1 == self.error_counter.get_errors()
        assert not self.changes.has_changed_in_last_minutes(1)

    def test_storing_events(self):

        cluster = {"id": "abcd", "name": "mycluster"}

        self.worker.store_events_for_cluster(cluster)

        self.cluster_repo_mock.get_cluster_hosts.assert_called_once()
        self.event_repo_mock.get_cluster_events.assert_called_once()
        self.cluster_events_storage_mock.store.assert_called_once()

        assert 0 == self.error_counter.get_errors()
        assert self.changes.has_changed_in_last_minutes(1)

    def test_storing_events_cluster_with_hosts(self):

        cluster = {"id": "abcd", "name": "mycluster", "hosts": ["1", "2", "3"]}

        self.worker.store_events_for_cluster(cluster)

        self.cluster_repo_mock.get_cluster_hosts.assert_not_called()
        self.event_repo_mock.get_cluster_events.assert_called_once()
        self.cluster_events_storage_mock.store.assert_called_once()

        assert 0 == self.error_counter.get_errors()
        assert self.changes.has_changed_in_last_minutes(1)

    def test_storing_events_cluster_with_empty_hosts(self):
        cluster = {"id": "abcd", "name": "mycluster", "hosts": []}

        self.worker.store_events_for_cluster(cluster)

        self.cluster_repo_mock.get_cluster_hosts.assert_called_once()
        self.event_repo_mock.get_cluster_events.assert_called_once()
        self.cluster_events_storage_mock.store.assert_called_once()

        assert 0 == self.error_counter.get_errors()
        assert self.changes.has_changed_in_last_minutes(1)

    def test_retrieving_events_from_queue(self):
        cluster = {"id": "abcd", "name": "mycluster"}

        self.queue.put(cluster)
        self.worker.consume_queue()
        self.queue.join()

        self.cluster_repo_mock.get_cluster_hosts.assert_called_once()
        self.event_repo_mock.get_cluster_events.assert_called_once()
        self.cluster_events_storage_mock.store.assert_called_once()

        assert 0 == self.error_counter.get_errors()
        assert self.changes.has_changed_in_last_minutes(1)
