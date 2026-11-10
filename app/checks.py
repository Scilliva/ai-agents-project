"""Stage: the deterministic checks and the triage. Replaced in week 9.

Until you wire yours in, there are no checks, and the stub says so by
firing: a missing check must never look like a passed one. The triage
therefore never lets an invoice skip the approval gate.

To replace it, copy your `labs/week09/starter/checks.py` over this file (it
has no sibling imports), then move your `code_triage` and its
`AUTO_APPROVE_LIMIT_EUR` across from `labs/week09/starter/03_untrusted.py`.
Week 9's homework was to send a failed check to the week 8 gate, and that
is exactly what `pipeline.py` does with the triage's answer.

Keep these names and signatures, because `pipeline.py` calls them:

    GROUPS: dict[str, list[str]]
    CheckReport                       fired, parsed, clean
    run_checks(fields) -> CheckReport
    code_triage(fields, report) -> tuple[bool, str]
"""

from __future__ import annotations

from dataclasses import dataclass

from .stub import stub

GROUPS = {
    "identity": ["invoice_number", "purchase_order", "currency"],
    "amounts": ["net_amount", "vat_amount", "total_amount"],
}
ALL_FIELDS = [f for g in GROUPS.values() for f in g]


@dataclass
class CheckReport:
    fired: list[str]
    parsed: dict[str, float | None]

    @property
    def clean(self) -> bool:
        return not self.fired


@stub(week=9, does="fires: no checks exist, so nothing passes")
def run_checks(fields: dict[str, str | None]) -> CheckReport:
    return CheckReport(fired=["stub: no checks are wired in"],
                       parsed={"net": None, "vat": None, "total": None})


@stub(week=9, does="refuses: never lets an invoice skip the gate")
def code_triage(fields: dict, report) -> tuple[bool, str]:
    return False, "stub: no triage, every invoice goes to the gate"
