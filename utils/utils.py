import os


def get_env(env, default=None):
    res = os.environ.get(env, "").strip()
    if not res or res == '""':
        res = default
    return res
