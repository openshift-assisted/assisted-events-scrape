from datetime import datetime
from utils import ErrorCounter, Changes, get_dict_hash


class TestUtils:
    def test_changes(self):
        changes = Changes()
        today = datetime.today()
        assert not changes.has_changed_after(today)
        assert not changes.has_changed_in_last_minutes(1)

        changes.set_changed()
        assert changes.has_changed_after(today)
        assert changes.has_changed_in_last_minutes(1)

    def test_error_count(self):
        error_counter = ErrorCounter()
        assert 0 == error_counter.get_errors()
        error_counter.inc()
        assert 1 == error_counter.get_errors()
        error_counter.inc()
        error_counter.inc()
        assert 3 == error_counter.get_errors()

    def test_dict_hash(self):
        master_version = {
            "release_tag": "master",
            "versions": {
                "assisted-installer":
                "registry-proxy.engineering.redhat.com/rh-osbs/openshift4-assisted-installer-rhel8:latest"
            }
        }
        specific_version = {
            "release_tag": "v2.3.0",
            "versions": {
                "assisted-installer":
                "registry-proxy.engineering.redhat.com/rh-osbs/openshift4-assisted-installer-rhel8:v1.0.0-151"
            }
        }

        assert get_dict_hash(master_version) != get_dict_hash(specific_version)
        assert get_dict_hash(specific_version) == get_dict_hash(specific_version)

    def test_filtered_hash(self):
        cluster_A = {
            "id": "d386f7df-03ba-46bf-a49b-f6b65a0fb90d",
            "status_updated_at": "2022-03-08T13:15:29.553Z",
            "updated_at": "2022-03-27T11:25:07.052462Z",
            "created_at": "2022-03-23T00:25:07.052462Z",
            "hosts": [
                {
                    "cluster_id": "d386f7df-03ba-46bf-a49b-f6b65a0fb90d",
                    "progress": {
                        "current_stage": None,
                        "stage_started_at": "0001-01-01T00:00:00.000Z",
                        "stage_updated_at": "0001-01-01T00:00:00.000Z"
                    }
                }
            ]
        }
        cluster_B = {
            "id": "a386f7df-03ba-46bf-a49b-f6b65a0fb90c",
            "status_updated_at": "2022-03-08T13:15:29.553Z",
            "updated_at": "2022-03-27T11:25:07.052462Z",
            "created_at": "2022-03-23T00:25:07.052462Z",
            "hosts": [
                {
                    "cluster_id": "a386f7df-03ba-46bf-a49b-f6b65a0fb90c",
                    "progress": {
                        "current_stage": None,
                        "stage_started_at": "0001-01-01T00:00:00.000Z",
                        "stage_updated_at": "0001-01-01T00:00:00.000Z"
                    }
                }
            ]
        }
        cluster_C = {
            "id": "d386f7df-03ba-46bf-a49b-f6b65a0fb90d",
            "status_updated_at": "2021-03-08T13:15:29.553Z",
            "updated_at": "2021-03-27T11:25:07.052462Z",
            "created_at": "2021-03-23T00:25:07.052462Z",
            "hosts": [
                {
                    "cluster_id": "d386f7df-03ba-46bf-a49b-f6b65a0fb90d",
                    "progress": {
                        "current_stage": None,
                        "stage_started_at": "0001-01-01T00:00:00.000Z",
                        "stage_updated_at": "0001-01-01T00:00:00.000Z"
                    }
                }
            ]
        }
        ignore_fields = ["updated_at", "created_at", "status_updated_at"]
        assert get_dict_hash(cluster_A) != get_dict_hash(cluster_B)
        assert get_dict_hash(cluster_A) == get_dict_hash(cluster_A)
        hash_A = get_dict_hash(cluster_A, ignore_fields=ignore_fields)
        hash_C = get_dict_hash(cluster_C, ignore_fields=ignore_fields)
        assert hash_A == hash_C
