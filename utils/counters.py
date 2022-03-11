import threading
from datetime import datetime
from datetime import timedelta


class ErrorCounter:
    def __init__(self):
        self.lock = threading.Lock()
        self.value = 0

    def inc(self) -> None:
        with self.lock:
            self.value += 1

    def get_errors(self) -> None:
        with self.lock:
            return self.value


class Changes:
    def __init__(self):
        self.lock = threading.Lock()
        self.last_update = None

    def set_changed(self) -> None:
        with self.lock:
            self.last_update = datetime.now()

    def has_changed_after(self, changed_after: datetime) -> bool:
        with self.lock:
            if self.last_update is None:
                return False
            return self.last_update >= changed_after

    def has_changed_in_last_minutes(self, minutes: timedelta) -> bool:
        with self.lock:
            if self.last_update is None:
                return False
            return self.last_update + timedelta(minutes=minutes) > datetime.now()
