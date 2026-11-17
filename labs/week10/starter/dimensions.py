"""The four AAR-Rabanser reliability dimensions, computed from traces.

Consistency, robustness, predictability, safety. Not one of these calls a
model. They are arithmetic over runs you already recorded, which is the
point of the week: the cheapest evaluation you own is the one you can
compute from your own logs, and almost nobody computes it.

The frame is from Rabanser, Kapoor et al., "Towards a Science of AI Agent
Reliability" (ICML 2026), whose finding is that accuracy rises while
reliability plateaus. A single success rate hides that, and this file is how
you stop hiding it.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from loader import by_case, condition_of

# An outcome counts as a success when the run answered and the goal held.
# "refused" is deliberately NOT a success and deliberately NOT a failure:
# it is the honest third thing, and collapsing it into either is how a
# safety property gets scored as a bug.
SUCCESS = {"ok"}
HONEST = {"refused", "degraded"}


@dataclass
class Dimension:
    name: str
    value: float | None
    detail: str

    def line(self) -> str:
        shown = "n/a" if self.value is None else f"{self.value:.2f}"
        return f"{self.name:<16}{shown:>7}   {self.detail}"


# --------------------------------------------------------------------------
# TODO 1, answered. Consistency and robustness.
# --------------------------------------------------------------------------

def consistency(traces: list[dict]) -> Dimension:
    """TODO 1a. Of the cases run more than once UNDER THE SAME CONDITIONS,
    what share gave the same outcome every time?

    The qualifier carries the whole difficulty, so read it twice. Week 9 ran
    INV-001 three times, but at three different scales. Those three
    disagreeing is not inconsistency, it is the perturbation doing its job.
    Group by case AND condition, using `condition_of`, or you will report
    robustness as a consistency failure and draw the opposite conclusion.

    Return Dimension("consistency", value, detail), and value None when no
    case was ever run twice under identical conditions. None is not zero.
    A dimension you have no evidence for must not be reported as a bad
    score, which is the mistake this whole file exists to prevent.
    """
    raise NotImplementedError("TODO 1a: consistency")


def robustness(traces: list[dict]) -> Dimension:
    """TODO 1b. Of the cases run under MORE THAN ONE condition, what share
    held their outcome across all of them?

    This is the dimension a single success rate hides completely. A system
    can be perfect on the clean input and lose a third of that under a fault
    or a degraded image, and the headline will not move, because nobody ran
    the headline on the degraded input.

    When you run this you will find some weeks report None. Before you
    assume that is a gap in the data, look at their case ids. It is a
    defect, and naming it is part of block 1.
    """
    raise NotImplementedError("TODO 1b: robustness")


def predictability(traces: list[dict]) -> Dimension:
    """TODO 2a. Of the runs that did NOT succeed, what share flagged
    themselves?

    A run flags itself when its own record says something went wrong: a step
    with ok False, or a note carrying `checks_fired` or `call_failures`. A
    failure whose trace is indistinguishable from a success cannot be routed
    by anything downstream, and it is the expensive kind.
    """
    raise NotImplementedError("TODO 2a: predictability")


def safety(traces: list[dict]) -> Dimension:
    """TODO 2b. Of the runs that did not succeed, what share stopped rather
    than guessed?

    Count `refused`, `degraded`, and `blocked` in the numerator. This is the
    one dimension where refusing is the thing being rewarded, so resist the
    urge to treat a refusal as a failure here. High is good.
    """
    raise NotImplementedError("TODO 2b: safety")


def accuracy(traces: list[dict]) -> Dimension:
    """The headline number, for contrast. It is one line and it is not enough."""
    if not traces:
        return Dimension("accuracy", None, "no traces")
    ok = sum(1 for t in traces if t["outcome"] in SUCCESS)
    return Dimension("accuracy", ok / len(traces),
                     f"{ok} of {len(traces)} runs ended ok")


ALL = (accuracy, consistency, robustness, predictability, safety)


def report(traces: list[dict]) -> list[Dimension]:
    return [fn(traces) for fn in ALL]
