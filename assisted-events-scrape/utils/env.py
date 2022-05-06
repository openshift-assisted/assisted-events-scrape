import os


def get_env(key, mandatory=False, default=None):
    res = os.environ.get(key, default)
    if res == "":
        res = default

    if res:
        res = res.strip()
    elif mandatory:
        raise ValueError(f'Mandatory environment variable is missing: {key}')

    return res
