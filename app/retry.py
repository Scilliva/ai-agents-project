"""Stage: retries, fallback, and the degrade path. Replaced in week 8.

Until you wire yours in, there is no policy: every step is called exactly
once, nothing is retried, no fallback is tried, and an exception propagates.
That is the week 8 baseline, the run you recorded before fixing anything.

To replace it, copy your `labs/week08/starter/retry.py` and `faults.py`
into `app/`, then change the sibling import in `retry.py`:

    from faults import ContractDrift, RateLimited, ServerError, ToolTimeout
    from .faults import ContractDrift, RateLimited, ServerError, ToolTimeout

Keep these names and signatures, because `pipeline.py` calls them:

    StepPolicy, Attempt, StepResult
    is_retryable(exc) -> bool
    call_with_policy(fn, *args, policy, fallback=None, validate=None,
                     **kwargs) -> StepResult

The policies themselves live in `pipeline.py`, one per step, because the
lecture's rule is to choose them per step, in advance, by consequence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .stub import stub


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


@stub(week=8, does="retries nothing")
def is_retryable(exc: BaseException) -> bool:
    return False


@stub(week=8, does="pass-through: one attempt, no fallback, errors propagate")
def call_with_policy(fn, *args, policy: StepPolicy, fallback=None,
                     validate=None, **kwargs) -> StepResult:
    value = fn(*args, **kwargs)
    return StepResult(value=value, ok=True, attempts=[Attempt(1, None)])
