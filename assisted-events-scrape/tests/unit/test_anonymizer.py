from utils import Anonymizer


class TestAnonymizer:
    def test_anonymize_infra_env(self):
        infra_env = {
            "id": "efeb91a5-2f41-4425-a835-c4b75a0ceb37",
            "user_name": "myuser"
        }
        Anonymizer.anonymize_infra_env(infra_env)
        assert "user_name" not in infra_env
        assert "user_id" in infra_env

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
