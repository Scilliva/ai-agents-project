"""The harness that breaks things on purpose. Given complete.

You do not write this file, you aim it.

The degradation path is the least tested code in any system, because it only
runs when something is already broken. If you cannot force it on demand, you
have written it and never seen it execute.

Deterministic by construction: given a seed, a tool name, and a call index,
the same fault fires on the same call every time. A failure you cannot
reproduce is a failure you cannot claim to have fixed.

    python 01_survive.py --faults "search:timeout@1.0"
    python 01_survive.py --faults "search:timeout@0.5,fees:drift@1.0"
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field

FAULTS = {
    "timeout": "the call never returns within the deadline",
    "rate_limit": "429, the upstream is asking you to slow down",
    "server_error": "500, the upstream is broken",
    "malformed": "200, and the body is not what the contract says",
    "empty": "200, and the result is empty. Not an error. Is it a failure?",
    "slow": "200, eventually. Four times the usual latency.",
    "drift": "200, valid, and a field has been renamed. No retry fixes this.",
    "flaky": "fails once, then succeeds. The reason retries exist at all.",
}


class ToolTimeout(Exception):
    """The call did not return in time."""


class RateLimited(Exception):
    """429. Retryable, and only after a wait."""


class ServerError(Exception):
    """500. Retryable, up to a point."""


class ContractDrift(Exception):
    """The response validated as JSON and not as our contract.

    Raised by YOUR validation, never by the transport. That is the whole
    point of this fault: the call succeeded.
    """


@dataclass
class FaultPlan:
    """Which fault fires on which call, decided in advance."""

    seed: int = 42
    rules: dict[str, tuple[str, float]] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)
    fired: list[str] = field(default_factory=list)

    @classmethod
    def parse(cls, spec: str, seed: int = 42) -> "FaultPlan":
        """`--faults "search:timeout@0.5,fees:drift@1.0"`"""
        rules = {}
        for part in filter(None, (s.strip() for s in spec.split(","))):
            target, _, rest = part.partition(":")
            kind, _, rate = rest.partition("@")
            if kind not in FAULTS:
                raise SystemExit(f"unknown fault {kind!r}. "
                                 f"Known: {sorted(FAULTS)}")
            rules[target.strip()] = (kind.strip(), float(rate or 1.0))
        return cls(seed=seed, rules=rules)

    def _fires(self, tool: str, index: int, rate: float) -> bool:
        digest = hashlib.sha256(
            f"{self.seed}:{tool}:{index}".encode()).hexdigest()
        return (int(digest[:8], 16) % 1000) / 1000.0 < rate

    def apply(self, tool: str, value):
        """Called by every tool, before it returns. Raises or mutates."""
        rule = self.rules.get(tool)
        if not rule:
            return value
        kind, rate = rule
        index = self.counts.get(tool, 0)
        self.counts[tool] = index + 1
        if not self._fires(tool, index, rate):
            return value

        self.fired.append(f"{tool}:{kind}#{index}")
        if kind == "timeout":
            raise ToolTimeout(f"{tool} timed out")
        if kind == "rate_limit":
            raise RateLimited(f"{tool} rate limited")
        if kind == "server_error":
            raise ServerError(f"{tool} returned 500")
        if kind == "flaky":
            if index == 0:
                raise ServerError(f"{tool} returned 500 (flaky, first call)")
            return value
        if kind == "slow":
            time.sleep(0.4)
            return value
        if kind == "empty":
            return [] if isinstance(value, list) else {}
        if kind == "malformed":
            return "<html>502 Bad Gateway</html>"
        if kind == "drift":
            # Valid, parseable, and the field has been renamed. Retrying
            # this a hundred times produces a hundred identical wrong
            # answers.
            if isinstance(value, dict):
                return {("amount_eur" if k == "fee_eur" else k): v
                        for k, v in value.items()}
        return value
