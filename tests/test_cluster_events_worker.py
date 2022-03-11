import unittest
import logging
from queue import Queue
from unittest.mock import Mock
from workers.cluster_events_worker import ClusterEventsWorker
from utils.counters import ErrorCounter
from utils.counters import Changes


class TestClusterEventsWorker(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.queue = Queue()
        self.cluster_repo_mock = Mock()
        self.event_repo_mock = Mock()
        self.cluster_events_storage_mock = Mock()
        self.error_counter = ErrorCounter()
        self.changes = Changes()
        self.worker = ClusterEventsWorker(
            "Test Worker", self.queue, self.cluster_repo_mock,
            self.event_repo_mock, self.cluster_events_storage_mock,
            self.error_counter, self.changes, False)

    def test_error_getting_cluster(self):
        self.cluster_repo_mock.get_cluster.side_effect = Exception("Error getting cluster")

        self.worker.store_events_for_cluster("abc")
        self.event_repo_mock.get_cluster_events.assert_not_called()
        self.cluster_events_storage_mock.store.assert_not_called()

        self.assertEqual(1, self.error_counter.get_errors())
        self.assertFalse(self.changes.has_changed_in_last_minutes(1))

    def test_error_getting_events(self):
        self.event_repo_mock.get_cluster_events.side_effect = Exception("Error getting cluster")

        self.worker.store_events_for_cluster("abc")
        self.cluster_repo_mock.get_cluster.assert_called_once()
        self.cluster_events_storage_mock.store.assert_not_called()

        self.assertEqual(1, self.error_counter.get_errors())
        self.assertFalse(self.changes.has_changed_in_last_minutes(1))

    def test_error_storing_events(self):
        self.cluster_events_storage_mock.store.side_effect = Exception("Error getting cluster")

        self.worker.store_events_for_cluster("abc")
        self.cluster_repo_mock.get_cluster.assert_called_once()
        self.event_repo_mock.get_cluster_events.assert_called_once()

        self.assertEqual(1, self.error_counter.get_errors())
        self.assertFalse(self.changes.has_changed_in_last_minutes(1))

    def test_storing_events(self):

        self.worker.store_events_for_cluster("abc")
        self.cluster_repo_mock.get_cluster.assert_called_once()
        self.event_repo_mock.get_cluster_events.assert_called_once()
        self.cluster_events_storage_mock.store.assert_called_once()

        self.assertEqual(0, self.error_counter.get_errors())
        self.assertTrue(self.changes.has_changed_in_last_minutes(1))
