from utils import Anonymizer


class TestAnonymizer:
    def test_hash_user_name(self):
        cluster = {
            "id": "efeb91a5-2f41-4425-a835-c4b75a0ceb37",
            "user_name": "myuser"
        }
        Anonymizer.anonymize_cluster(cluster)
        assert "user_name" not in cluster
        assert "user_id" in cluster

    def test_hash_no_user_name(self):
        cluster = {
            "id": "efeb91a5-2f41-4425-a835-c4b75a0ceb37"
        }
        Anonymizer.anonymize_cluster(cluster)
        assert "user_name" not in cluster
        assert "user_id" not in cluster

    def test_hash_empty_user_name(self):
        cluster = {
            "id": "efeb91a5-2f41-4425-a835-c4b75a0ceb37",
            "user_name": ""
        }
        Anonymizer.anonymize_cluster(cluster)
        assert "user_name" not in cluster
        assert "user_id" in cluster
        assert cluster["user_id"] is None
