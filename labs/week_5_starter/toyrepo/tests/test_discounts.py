"""Tests for the individual discounts. Do not weaken them."""

import unittest

from booking import Booking
from discounts import (club_discount, off_peak_discount, resident_discount,
                       total_discount)


class TestDiscounts(unittest.TestCase):

    def test_resident(self):
        self.assertAlmostEqual(resident_discount(Booking(hours=1, resident=True)), 0.10)
        self.assertAlmostEqual(resident_discount(Booking(hours=1)), 0.0)

    def test_club(self):
        self.assertAlmostEqual(club_discount(Booking(hours=1, club=True)), 0.15)

    def test_off_peak_late_evening(self):
        self.assertAlmostEqual(
            off_peak_discount(Booking(hours=1, start_hour=22)), 0.20)

    def test_daytime_is_not_off_peak(self):
        self.assertAlmostEqual(
            off_peak_discount(Booking(hours=1, start_hour=19)), 0.0)

    def test_total_is_capped(self):
        booking = Booking(hours=1, resident=True, club=True, start_hour=22)
        self.assertAlmostEqual(total_discount(booking), 0.30)


if __name__ == "__main__":
    unittest.main()
