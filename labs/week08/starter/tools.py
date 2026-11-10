"""The three tools the pipeline calls. Given complete, and offline.

No model, no network, no key. That is deliberate: blocks 1 and 2 of this
session are about what your code does when a dependency misbehaves, and
putting a real model in the way would add a second source of failure you
would then have to rule out.

Every tool routes its return value through `plan.apply`, which is where the
harness gets to break it.
"""

from __future__ import annotations

from faults import FaultPlan

CASES = {
    "RB-2026-0042": {"subject": "A. Muller", "topic": "parking vignette"},
    "RB-2026-0043": {"subject": "B. Weber", "topic": "waste collection"},
}
HANDBOOK = {
    "parking vignette": "The resident parking vignette costs 60 EUR a year.",
    "waste collection": "A 120 litre bin costs 5.20 EUR per collection.",
}
FEES = {"parking vignette": {"fee_eur": 60.0, "period": "year"},
        "waste collection": {"fee_eur": 5.20, "period": "collection"}}


def search(plan: FaultPlan, topic: str):
    """The primary lookup. Returns a list of passages."""
    hit = HANDBOOK.get(topic)
    return plan.apply("search", [hit] if hit else [])


def keyword_fallback(plan: FaultPlan, topic: str):
    """The cheaper, worse alternative. Never faulted, on purpose.

    A fallback that fails as often as the thing it backs up is not a
    fallback. This one is always available and always less good, which is
    the trade you are actually making.
    """
    hit = HANDBOOK.get(topic)
    return [f"(cached) {hit}"] if hit else []


def fees(plan: FaultPlan, topic: str):
    """The structured lookup. This is the one contract drift hits."""
    return plan.apply("fees", dict(FEES.get(topic, {})))
