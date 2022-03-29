from datetime import datetime
from utils import ErrorCounter, Changes


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
