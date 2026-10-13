"""The booking record. One immutable value object, no behaviour."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Booking:
    """One reservation of one hall.

    hours       how long the hall is booked for, in hours
    hall        "main" or "annex"
    start_hour  the hour the booking starts, 0 to 23, local time
    resident    the person booking lives in Remerbaach
    club        the booking is made by a registered club
    """

    hours: float
    hall: str = "main"
    start_hour: int = 10
    resident: bool = False
    club: bool = False
