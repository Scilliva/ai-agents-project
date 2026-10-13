# hallbooking

A very small library that prices bookings of the sports halls run by
Remerbaach, a fictional Luxembourg commune. It exists so that an agent has
somewhere real to work.

There are no dependencies. Everything is standard library Python 3.12.

## Running the tests

```bash
cd toyrepo
python run_tests.py
```

One test fails on a clean checkout. That is deliberate.

## Layout

| File | What it holds |
| `booking.py` | The `Booking` record: hours, hall, start hour, resident, club |
| `discounts.py` | The discount rates and one function per discount |
| `pricing.py` | The total, including the minimum charge and VAT |
| `report.py` | A one line human readable summary of a booking |
| `tests/` | Sixteen tests. Do not weaken them. |
| `run_tests.py` | The runner. Exit code 0 means everything passed. |

## The rules being implemented

- The hourly rate depends on the hall: 40 euros for the main hall, 25 for the annex.
- A resident of Remerbaach gets 10 percent off.
- A booking that starts at 20:00 or later is off peak and gets 20 percent off.
- A registered club gets 15 percent off.
- Discounts add up, and the total discount is capped at 30 percent.
- There is a minimum charge of 15 euros before VAT.
- VAT is 17 percent and the final amount is rounded to two decimal places.

## Known issues

1. The off peak rule is not applied to a booking that starts exactly at 20:00,
   although the rules above say it should be. There is a failing test.
2. The discount rates are written out in four places: `discounts.py`,
   `pricing.py`, and twice in `report.py`. Changing a rate currently means
   remembering all four.
