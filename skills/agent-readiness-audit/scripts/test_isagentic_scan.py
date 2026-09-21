import unittest
from datetime import datetime, timezone

from isagentic_scan import is_fresh

START = datetime(2026, 9, 21, 10, 33, tzinfo=timezone.utc)


class FreshnessTest(unittest.TestCase):
    def test_stale_snapshot_rejected(self):
        self.assertFalse(is_fresh("2026-08-28T11:34:46.152Z", START))

    def test_scan_after_start_accepted(self):
        self.assertTrue(is_fresh("2026-09-21T10:34:08.444Z", START))

    def test_small_clock_skew_tolerated(self):
        self.assertTrue(is_fresh("2026-09-21T10:32:00Z", START))


if __name__ == "__main__":
    unittest.main()
