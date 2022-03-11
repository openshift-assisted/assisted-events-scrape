import unittest

from utils.counters import ErrorCounter
from utils.counters import Changes
from datetime import datetime


class TestUtils(unittest.TestCase):
    def test_changes(self):
        changes = Changes()
        today = datetime.today()
        self.assertFalse(changes.has_changed_after(today))
        self.assertFalse(changes.has_changed_in_last_minutes(1))

        changes.set_changed()
        self.assertTrue(changes.has_changed_after(today))
        self.assertTrue(changes.has_changed_in_last_minutes(1))

    def test_error_count(self):
        error_counter = ErrorCounter()
        self.assertEqual(0, error_counter.get_errors())
        error_counter.inc()
        self.assertEqual(1, error_counter.get_errors())
        error_counter.inc()
        error_counter.inc()
        self.assertEqual(3, error_counter.get_errors())
