"""Tests for the total. These encode the published rules. Do not weaken them."""

import unittest

from booking import Booking
from pricing import base_eur, net_eur, total_eur


class TestBase(unittest.TestCase):

    def test_main_hall_rate(self):
        self.assertAlmostEqual(base_eur(Booking(hours=2)), 80.0)

    def test_annex_rate(self):
        self.assertAlmostEqual(base_eur(Booking(hours=2, hall="annex")), 50.0)

    def test_unknown_hall_raises(self):
        with self.assertRaises(ValueError):
            base_eur(Booking(hours=1, hall="pool"))


class TestTotal(unittest.TestCase):

    def test_plain_booking_adds_vat(self):
        self.assertEqual(total_eur(Booking(hours=2)), 93.60)

    def test_minimum_charge_applies(self):
        # 0.5h in the annex is 12.50, below the 15.00 floor.
        self.assertEqual(net_eur(Booking(hours=0.5, hall="annex")), 15.0)
        self.assertEqual(total_eur(Booking(hours=0.5, hall="annex")), 17.55)

    def test_resident_discount(self):
        self.assertEqual(total_eur(Booking(hours=2, resident=True)), 84.24)

    def test_off_peak_starts_at_twenty(self):
        # The published rule is "20:00 or later", so a booking starting at
        # exactly 20:00 is off peak. Resident 10% plus off peak 20% is 30%.
        self.assertEqual(
            total_eur(Booking(hours=2, resident=True, start_hour=20)), 65.52)

    def test_off_peak_after_twenty(self):
        self.assertEqual(
            total_eur(Booking(hours=2, resident=True, start_hour=21)), 65.52)

    def test_discount_cap(self):
        # 10 + 20 + 15 is 45, capped at 30, so the same as the case above.
        self.assertEqual(
            total_eur(Booking(hours=2, resident=True, club=True,
                              start_hour=21)), 65.52)


if __name__ == "__main__":
    unittest.main()
