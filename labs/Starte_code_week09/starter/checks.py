"""Checks that need no human to look at the image, and the outcome table.

When the input was text you could always go and read the source. When the
input is an image, checking an extraction means looking at the image, and
nobody looks at ten thousand images. These functions are the only eyes the
system has.

Every check here is a function. None of them calls a model. That is the week
4 lesson in a new costume: the cheapest critic is a function, and a judge
that shares the extractor's blind spot is not a control.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

GROUPS = {
    "identity": ["invoice_number", "purchase_order", "currency"],
    "amounts": ["net_amount", "vat_amount", "total_amount"],
}
ALL_FIELDS = [f for g in GROUPS.values() for f in g]

VAT_RATE = 0.17
INVOICE_RE = re.compile(r"^INV-\d{3}-LU$")
PO_RE = re.compile(r"^PO-\d{4}-\d{4}$")
CURRENCIES = {"EUR"}


def parse_amount(text: str | None) -> float | None:
    """Luxembourg prints one thousand as `1 129.23`. `float()` refuses it.

    Note what this does NOT do: it does not strip every space and hope. A
    space is removed only where it separates a digit from a group of exactly
    three, which is what a thousands separator is. Strip blindly instead and
    "12 34 56" becomes 123456, which is three numbers welded into one, and
    no later check will ever tell you that happened.
    """
    if text is None:
        return None
    s = str(text).replace("\u00a0", " ").replace("EUR", "").strip()
    # A thousands separator groups digits in THREES. Requiring that is what
    # separates "1 129.23", which is one number, from "12 34 56", which is
    # three numbers that a blind strip would silently weld into 123456.
    s = re.sub(r"(?<=\d) (?=\d{3}\b)", "", s)
    if "," in s and "." in s:
        s = s.replace(",", "")           # 1,129.23
    elif re.fullmatch(r"-?\d+,\d{1,2}", s):
        s = s.replace(",", ".")          # 1129,23
    if not re.fullmatch(r"-?\d+(\.\d{1,2})?", s):
        return None
    return round(float(s), 2)


@dataclass
class CheckReport:
    fired: list[str]
    parsed: dict[str, float | None]

    @property
    def clean(self) -> bool:
        return not self.fired


# --------------------------------------------------------------------------
# TODO 3, answered. Four checks, all deterministic, none of them a model.
# --------------------------------------------------------------------------

def run_checks(fields: dict[str, str | None]) -> CheckReport:
    """TODO 3. Every check that runs without a human looking at the image.

    Append one short string to `fired` for each problem found, and return a
    CheckReport carrying the parsed amounts as well, because block 1 needs
    the numbers and not only the verdicts.

    Build these four, cheapest first, and none of them may call a model:

      1. Arithmetic. net + vat == total, to the cent. One line, and it
         catches a whole class of misreadings including a value read from
         the wrong column of a two-column invoice.
      2. VAT rate. vat / net should be VAT_RATE for this supplier.
      3. Format. INVOICE_RE, PO_RE, and CURRENCIES give the shapes this
         supplier always uses. Remember that a missing purchase order is
         legitimate on one of these invoices, so None must not fire.
      4. Plausibility. Is the total in a range this supplier could invoice?

    A warning worth taking seriously: an arithmetic check catches
    INCONSISTENCY, not error. Three amounts that are all wrong but agree
    with each other will pass every one of these. Try it on paper before
    you decide your checks are finished.
    """
    raise NotImplementedError("TODO 3: run_checks")


# --------------------------------------------------------------------------
# The outcome table. This is the measurement the session exists to produce.
# --------------------------------------------------------------------------

OUTCOMES = ("correct", "WRONG", "caught", "refused", "false_alarm")


def classify(truth: dict, report: CheckReport) -> str:
    """Five outcomes. Only one of them is a silent bad extraction.

    correct      every amount right, checks silent. What you wanted.
    false_alarm  every amount right, checks fired. A check that cries wolf
                 costs a human's attention, so it is a defect too, and a
                 cheap one to measure.
    caught       an amount wrong, checks fired. The system working.
    WRONG        an amount wrong, checks silent. THIS is the column that
                 matters, and it is the only row a human would have had to
                 open the image to find.
    refused      no usable amount came back, which is at least honest.

    Judged on all three amounts rather than on the total alone. A run that
    reads the total correctly out of the wrong column, and the net out of
    the wrong column too, is not a correct extraction, and scoring only the
    total would call it one.
    """
    got = report.parsed
    pairs = (("net", "net_amount"), ("vat", "vat_amount"),
             ("total", "total_amount"))

    # A value that came back and disagrees with the truth is an error, and it
    # is judged FIRST. Checking "did the total come back" first instead looks
    # reasonable and is wrong: a run that refuses the total while quietly
    # misreading the net would be filed as an honest refusal. That happens
    # for real on this corpus, on INV-003 under compression, where the net
    # comes back as 955.15 rather than 965.15 and the total comes back null.
    wrong = [f for k, f in pairs
             if got[k] is not None and abs(got[k] - truth[f]) >= 0.01]
    if wrong:
        return "WRONG" if report.clean else "caught"

    if any(got[k] is None for k, _ in pairs):
        return "refused"

    return "correct" if report.clean else "false_alarm"


def tally(rows: list[dict]) -> dict[str, int]:
    return {o: sum(1 for r in rows if r.get("outcome") == o) for o in OUTCOMES}
