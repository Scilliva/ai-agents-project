"""A one line human readable summary of a booking, for the confirmation email."""

from booking import Booking
from pricing import base_eur, total_eur

# The same four rates again, as display strings this time. Task B asks you to
# derive these from one source rather than typing them out here.
RATE_LABELS = {
    "resident": "10%",
    "off_peak": "20%",
    "club": "15%",
    "cap": "30%",
}


def applied_labels(booking: Booking) -> list:
    """Which discount labels apply to this booking."""

    labels = []
    if booking.resident:
        labels.append("resident " + RATE_LABELS["resident"])
    if booking.start_hour >= 20:
        labels.append("off peak " + RATE_LABELS["off_peak"])
    if booking.club:
        labels.append("club " + RATE_LABELS["club"])
    return labels


def confirmation_line(booking: Booking) -> str:
    """One line, as it appears in the confirmation email."""

    labels = applied_labels(booking)
    applied = ", ".join(labels) if labels else "no discount"
    return (f"{booking.hall} hall, {booking.hours:g}h from {booking.start_hour:02d}:00, "
            f"base {base_eur(booking):.2f} EUR, {applied}, "
            f"total {total_eur(booking):.2f} EUR incl. VAT")
