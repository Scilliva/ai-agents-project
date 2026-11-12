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

from .faults import ContractDrift, RateLimited, ServerError, ToolTimeout


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
    return isinstance(exc, (ToolTimeout, RateLimited, ServerError))


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
    if policy.attempts < 1:
        raise ValueError("policy.attempts must be at least 1")
    if policy.max_elapsed < 0 or policy.base_delay < 0:
        raise ValueError("policy delays and elapsed limit must be non-negative")
    if policy.on_exhausted not in {"degrade", "escalate"}:
        raise ValueError("policy.on_exhausted must be 'degrade' or 'escalate'")

    started = time.monotonic()
    result = StepResult()
    last_error: BaseException | None = None

    for n in range(1, policy.attempts + 1):
        try:
            value = fn(*args, **kwargs)
            if validate is not None:
                validate(value)
        except Exception as exc:  # the policy classifies known failures
            last_error = exc
            attempt = Attempt(n=n, error=f"{type(exc).__name__}: {exc}")
            result.attempts.append(attempt)

            # Contract drift and other non-transient failures go directly to
            # fallback/degradation. A retry cannot repair a successful call
            # whose response violates our contract.
            if not is_retryable(exc) or n >= policy.attempts:
                break

            elapsed = time.monotonic() - started
            remaining = policy.max_elapsed - elapsed
            if remaining <= 0:
                break

            delay = policy.base_delay * (2 ** (n - 1))
            if policy.jitter:
                delay = random.uniform(0.0, delay)
            if delay > remaining:
                break

            attempt.slept = delay
            if delay:
                time.sleep(delay)
            continue

        result.attempts.append(Attempt(n=n, error=None))
        result.value = value
        result.ok = True
        result.outcome = "ok"
        return result

    if fallback is not None:
        result.used_fallback = True
        try:
            value = fallback(*args, **kwargs)
            if validate is not None:
                validate(value)
        except Exception as exc:  # fallback also must satisfy the contract
            last_error = exc
        else:
            result.value = value
            result.ok = True
            result.outcome = "fallback"
            return result

    result.ok = False
    result.outcome = ("escalated" if policy.on_exhausted == "escalate"
                      else "degraded")
    # Keep a failure visible to callers that inspect the attempt list, even
    # when a fallback was attempted and also failed.
    if last_error is not None and result.attempts:
        result.attempts[-1].error = (
            f"{result.attempts[-1].error}; fallback failed: "
            f"{type(last_error).__name__}: {last_error}"
            if result.used_fallback else result.attempts[-1].error
        )
    return result
