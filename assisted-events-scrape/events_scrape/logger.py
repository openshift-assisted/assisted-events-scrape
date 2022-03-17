# -*- coding: utf-8 -*-
import logging
import sys
from pythonjsonlogger import jsonlogger


def get_custom_format() -> str:
    log_fields = [
        "asctime",
        "name",
        "levelname",
        "thread",
        "message",
        "pathname",
        "lineno",
    ]
    return " ".join([f"%({field})s" for field in log_fields])


logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

log = logging.getLogger()
log.setLevel(logging.DEBUG)

fmt = jsonlogger.JsonFormatter(get_custom_format())

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(fmt)

log.addHandler(ch)
