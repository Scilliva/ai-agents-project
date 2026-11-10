"""The retry ladder. TODO 1 and 2.

Four responses to a failing step, and the lecture's instruction is to choose
one per step IN ADVANCE, by consequence, and to record which one fired:

    retry     the same call again, because the failure looks transient
    fallback  a different, worse call that is more likely to work
    degrade   answer partially, and say what is missing
    escalate  stop and ask a human

The policy is data, not control flow. That is what lets the same pipeline
run with one attempt in a fast test and three in the lab, and it is what
makes the policy reviewable. A try and except at every call site is the
thing this replaces, and finding fourteen of them later is the reason.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from faults import ContractDrift, RateLimited, ServerError, ToolTimeout


@dataclass
class StepPolicy:
    attempts: int = 3
    base_delay: float = 0.05
    jitter: bool = True
    max_elapsed: float = 5.0
    on_exhausted: str = "degrade"       # or "escalate"


@dataclass
class Attempt:
    n: int
    error: str | None
    slept: float = 0.0


@dataclass
class StepResult:
    value: object = None
    ok: bool = False
    attempts: list[Attempt] = field(default_factory=list)
    used_fallback: bool = False
    outcome: str = "ok"                 # ok | fallback | degraded | escalated

    @property
    def tries(self) -> int:
        return len(self.attempts)


# --------------------------------------------------------------------------
# TODO 1. Which errors deserve a second call?
# --------------------------------------------------------------------------

def is_retryable(exc: BaseException) -> bool:
    """TODO 1. Draw a line you can defend.

    Three of the exceptions in faults.py say "the upstream is having a
    moment", and a moment is exactly what a retry buys. One of them does
    not, and putting it on the wrong side of this line is the mistake this
    session exists to catch: the call SUCCEEDED, the response was valid, and
    a field had been renamed. Retrying that produces the same valid, wrong
    response as fast as the network allows, and then reports a timeout that
    never happened.

    Record in DECISIONS.md which one you excluded and why. Then consider a
    401, which is not in this lab: retrying an authentication failure turns
    a broken credential into a slow broken credential, and on some upstreams
    into a locked account.
    """
    raise NotImplementedError("TODO 1: which errors are retryable")


# --------------------------------------------------------------------------
# TODO 2. Backoff with jitter, capped twice.
# --------------------------------------------------------------------------

def call_with_policy(fn, *args, policy: StepPolicy, fallback=None,
                     validate=None, **kwargs) -> StepResult:
    """TODO 2. Call `fn`, retrying by policy, then falling back, then degrading.

    Fill in a StepResult as you go: every attempt with its error, whether
    the fallback was used, and the final outcome. You report those counts at
    the checkpoint, and "it retried a few times" is not a count.

    Four things to get right.

    Two caps, not one. `attempts` bounds how many times you try and
    `max_elapsed` bounds how long the whole ladder may take. Without the
    second, three attempts with exponential backoff can still block a user
    for a minute.

    Exponential backoff: the delay doubles each time.

    Jitter, and it is not decoration. Ask what happens when thirty laptops
    in a room retry a rate limited endpoint at exactly the same interval.
    They re-collide, in lockstep, every time.

    `validate` runs on SUCCESS and is how contract drift is caught. It
    raises ContractDrift, which your `is_retryable` should refuse, so the
    ladder skips past retrying straight to the fallback. If you find
    yourself retrying a drifted response, TODO 1 is wrong.
    """
    raise NotImplementedError("TODO 2: the retry ladder")
