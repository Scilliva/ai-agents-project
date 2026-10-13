"""The discounts a booking can attract, and the cap that applies to the sum."""

from booking import Booking

# The rates. These four numbers are also written out by hand in pricing.py and
# again in report.py, which is the duplication task B asks you to remove.
RESIDENT_RATE = 0.10
OFF_PEAK_RATE = 0.20
CLUB_RATE = 0.15
MAX_TOTAL_DISCOUNT = 0.30

# A booking that starts at this hour or later is off peak.
OFF_PEAK_FROM_HOUR = 20


def is_off_peak(start_hour: int) -> bool:
    """True when a booking starting at `start_hour` counts as off peak.

    The published rule is "20:00 or later".
    """

    return start_hour > OFF_PEAK_FROM_HOUR


def resident_discount(booking: Booking) -> float:
    return 0.10 if booking.resident else 0.0


def off_peak_discount(booking: Booking) -> float:
    return 0.20 if is_off_peak(booking.start_hour) else 0.0


def club_discount(booking: Booking) -> float:
    return 0.15 if booking.club else 0.0


def total_discount(booking: Booking) -> float:
    """The sum of every discount that applies, capped."""

    total = (resident_discount(booking)
             + off_peak_discount(booking)
             + club_discount(booking))
    return min(total, 0.30)
