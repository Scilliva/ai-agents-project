"""Tests for the confirmation line. Do not weaken them."""

import unittest

from booking import Booking
from report import applied_labels, confirmation_line


class TestReport(unittest.TestCase):

    def test_no_discount_line(self):
        line = confirmation_line(Booking(hours=2))
        self.assertIn("main hall", line)
        self.assertIn("no discount", line)
        self.assertIn("incl. VAT", line)

    def test_labels_late_evening(self):
        labels = applied_labels(Booking(hours=1, resident=True, start_hour=22))
        self.assertEqual(labels, ["resident 10%", "off peak 20%"])


if __name__ == "__main__":
    unittest.main()
