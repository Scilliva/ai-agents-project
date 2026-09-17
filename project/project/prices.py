"""What this workload would cost on a hosted endpoint.

You are running locally, so your calls are free. That is convenient and it
is also a distortion, because in any job you take, tokens cost money and
somebody watches the bill. The syllabus asks you to justify design choices
in terms of cost as well as latency, reliability, and safety, so the course
keeps cost in view by making you estimate it.

An estimate is not a measurement, and you must label it as one. The habit
this file teaches is the same one the whole course teaches: a number
without its conditions is not evidence. Here the conditions are the price
list and the date it was read.

    from project.prices import estimate, PRICES
    est = estimate(input_tokens=1_200_000, output_tokens=90_000,
                   tier="mid")
    print(est.summary())

Prices below were read on the date in PRICE_DATE and they will be wrong by
the time you read this. Updating them is a legitimate way to earn
participation credit, and the update belongs in your DECISIONS.md with the
date you checked.
"""

from __future__ import annotations

from dataclasses import dataclass

PRICE_DATE = "2026-08-10"
CURRENCY = "EUR"

# Euros per million tokens. Three tiers rather than named products, because
# the argument this course cares about is "small model or large model", not
# "which vendor". Figures are rounded, indicative, and deliberately not
# attributed, so that nobody quotes them as a vendor comparison.
PRICES: dict[str, tuple[float, float]] = {
    # tier:   (input per 1M, output per 1M)
    "small":  (0.20, 0.80),
    "mid":    (2.50, 10.00),
    "large":  (12.00, 60.00),
    "embed":  (0.10, 0.00),
}


@dataclass(frozen=True)
class Estimate:
    tier: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float

    @property
    def total(self) -> float:
        return self.input_cost + self.output_cost

    @property
    def per_thousand(self) -> float:
        """The same call, a thousand times.

        One call is always about nothing, which is exactly why quoting the
        single call cost teaches nobody anything. Systems are billed by the
        thousand, so that is the unit this course reports in.
        """
        return self.total * 1000

    def summary(self) -> str:
        return (f"{self.per_thousand:.2f} {CURRENCY} per thousand calls on "
                f"the {self.tier} tier ({self.input_tokens:,} in, "
                f"{self.output_tokens:,} out per call), price list of "
                f"{PRICE_DATE}. Estimate, not a measurement.")


def estimate(input_tokens: int, output_tokens: int,
             tier: str = "small") -> Estimate:
    if tier not in PRICES:
        raise ValueError(f"tier must be one of {sorted(PRICES)}, got {tier!r}")
    in_rate, out_rate = PRICES[tier]
    return Estimate(tier=tier, input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    input_cost=input_tokens / 1e6 * in_rate,
                    output_cost=output_tokens / 1e6 * out_rate)


def estimate_traces(traces, tier: str = "small") -> Estimate:
    """Estimate what a set of recorded runs would have cost hosted.

    Takes anything with `total_tokens`, so it works on the Trace objects
    from `project.trace.read_traces`.
    """
    tin = sum(sum(s.input_tokens or 0 for s in t.steps) for t in traces)
    tout = sum(sum(s.output_tokens or 0 for s in t.steps) for t in traces)
    return estimate(tin, tout, tier)


def local_cost_note() -> str:
    """The sentence to put next to a local measurement, once per report."""
    return ("Run locally, so the monetary cost was zero. The costs that are "
            "real here are latency, resident memory, and the model size a "
            "student has to be able to run. The euro figures in this report "
            f"are estimates against the {PRICE_DATE} price list.")
