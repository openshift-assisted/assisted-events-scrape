import hashlib


def get_event_id(event_json) -> str:
    id_str = event_json["event_time"] + event_json["cluster_id"] + event_json["message"]
    _id = int(hashlib.md5(id_str.encode('utf-8')).hexdigest(), 16)
    return str(_id)
