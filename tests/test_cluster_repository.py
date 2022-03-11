import unittest
import copy

from repositories.cluster_repository import ClusterRepository
from unittest.mock import Mock


class TestClusterRepository(unittest.TestCase):
    def setUp(self):
        self.mock_hosts = [
            {"id": "123", "hostname": "foo"},
            {"id": "123", "hostname": "bar"},
        ]
        self.mock_clusters_list = [
            {"id": "abc"},
            {"id": "def"}
        ]
        self.client_mock = Mock()
        self.__set_expected_return_clusters_list()
        self.__set_expected_return_get_cluster_hosts()

    def tearDown(self):
        self.client_mock = None

    def __set_expected_return_clusters_list(self):
        self.client_mock.clusters_list = Mock(name='clusters_list', return_value=self.mock_clusters_list)

    def __set_expected_return_get_cluster_hosts(self):
        self.client_mock.get_cluster_hosts = Mock(name='get_cluster_hosts', return_value=self.mock_hosts)

    def test_list_cluster_ids(self):
        cr = ClusterRepository(self.client_mock)
        ids = cr.list_cluster_ids()
        self.client_mock.clusters_list.assert_called()
        assert(ids == ['abc', 'def'])

    def test_get_cluster(self):
        cr = ClusterRepository(self.client_mock)

        res = cr.get_cluster("abc")
        self.client_mock.clusters_list.assert_called_once()
        self.client_mock.get_cluster_hosts.assert_called()

        assert(res["id"] == "abc")

    def test_get_cluster_not_indexed(self):

        cr = ClusterRepository(self.client_mock)
        res = cr.get_cluster("zzz")

        assert(res is None)

    def test_get_cluster_not_cached(self):
        '''First upstream request doest not find it, but second will'''
        expected_cluster = {"id": "zzz"}
        second_list = self.mock_clusters_list
        second_list.append(copy.deepcopy(expected_cluster))

        expected_cluster["hosts"] = self.mock_hosts
        self.client_mock.clusters_list = Mock()
        self.client_mock.clusters_list.side_effect = [self.mock_clusters_list, second_list]
        cr = ClusterRepository(self.client_mock)
        res = cr.get_cluster("zzz")

        self.assertDictEqual(expected_cluster, res)
