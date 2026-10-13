"""What a booking costs, including the minimum charge and VAT."""

from booking import Booking
from discounts import total_discount

HALL_RATES = {"main": 40.0, "annex": 25.0}
MINIMUM_CHARGE_EUR = 15.0
VAT_RATE = 0.17


def base_eur(booking: Booking) -> float:
    """Hours times the hourly rate for the hall, before any discount."""

    if booking.hall not in HALL_RATES:
        raise ValueError("unknown hall: " + booking.hall)
    return HALL_RATES[booking.hall] * booking.hours


def net_eur(booking: Booking) -> float:
    """The amount after discounts, with the minimum charge applied."""

    net = base_eur(booking) * (1.0 - total_discount(booking))
    return max(net, MINIMUM_CHARGE_EUR)


def total_eur(booking: Booking) -> float:
    """The amount the customer pays, VAT included, rounded to two places."""

    return round(net_eur(booking) * (1.0 + VAT_RATE), 2)


def discount_summary(booking: Booking) -> str:
    """A short description of which discounts applied.

    The rates below are written out again here rather than imported, which is
    exactly the duplication task B asks you to remove.
    """

    parts = []
    if booking.resident:
        parts.append("resident 10%")
    if booking.start_hour > 20:
        parts.append("off peak 20%")
    if booking.club:
        parts.append("club 15%")
    if not parts:
        return "no discount"
    return ", ".join(parts) + " (capped at 30%)"
