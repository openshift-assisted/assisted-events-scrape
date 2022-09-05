import fnv


class Anonymizer:
    @classmethod
    def anonymize_cluster(cls, cluster: dict):
        cls._hash_user_name(cluster)

    @classmethod
    def anonymize_infra_env(cls, infra_env: dict):
        cls._hash_user_name(infra_env)

    @classmethod
    def _hash_user_name(cls, resource: dict):
        """mask user name with unique generated FNV-1a 128 bit id"""
        if "user_name" not in resource:
            return

        user_name = resource.pop("user_name")

        # empty username
        if not user_name:
            resource["user_id"] = None
        else:
            resource["user_id"] = str(fnv.hash(str(user_name).encode(), algorithm=fnv.fnv_1a, bits=128))
