import hashlib
import json
import copy
from typing import Iterable


def get_dict_hash(d: dict, ignore_fields: Iterable[str] = None) -> str:
    to_hash = copy.deepcopy(d)
    if ignore_fields:
        for field in ignore_fields:
            if field in to_hash:
                del to_hash[field]
    hashed_str = json.dumps(to_hash, default=str, sort_keys=True).encode('utf-8')
    return hashlib.sha256(hashed_str).hexdigest()
