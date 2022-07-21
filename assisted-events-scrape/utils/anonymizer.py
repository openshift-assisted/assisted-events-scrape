import fnv


class Anonymizer:
    @classmethod
    def anonymize_cluster(cls, cluster: dict):
        cls._hash_user_name(cluster)

    @classmethod
    def _hash_user_name(cls, cluster: dict):
        """mask user name with unique generated FNV-1a 128 bit id"""
        if "user_name" not in cluster:
            return

        user_name = cluster.get("user_name")
        del cluster["user_name"]

        # empty username
        if not user_name:
            cluster["user_id"] = None
        else:
            cluster["user_id"] = str(fnv.hash(str(user_name).encode(), algorithm=fnv.fnv_1a, bits=128))
