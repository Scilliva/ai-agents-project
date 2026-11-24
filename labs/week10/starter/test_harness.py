"""Block 3: the gates. This is the file that fails a build.

Everything so far printed tables. A table is a thing you read once. A test
is a thing that stops you shipping, and the difference between an
evaluation and a report is exactly this file.

    pytest -q                    # all gates
    pytest -q -m "not judged"    # the free ones only, no model calls

Note what is asserted and what is not. These gates assert properties that
should hold for ANY healthy version of the system, not the specific numbers
this week produced. A test pinned to 0.42 accuracy fails the moment somebody
improves something, gets deleted in week 12, and protects nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "project_spine"))

import judge as J
from dimensions import report
from loader import condition_of, load_goldset, load_traces, source_of

TRACES = load_traces()


# --------------------------------------------------------------------------
# The free gates. No model calls, so these can run on every commit.
# --------------------------------------------------------------------------

def test_traces_exist():
    assert TRACES, "no traces recorded. Week 10 has nothing to evaluate."


def test_every_trace_carries_its_conditions():
    """A number without its conditions is not evidence.

    This is the gate that would have caught the defect in the course's own
    artifacts, where week 9 recorded its run condition under two different
    keys in the same file.
    """
    missing = [t["trace_id"] for t in TRACES
               if not t.get("conditions", {}).get("model")
               or not t["conditions"].get("run_date")]
    assert not missing, f"{len(missing)} traces without model or run_date"


def test_condition_keys_are_consistent_within_a_week():
    """One fact, one home. Two spellings of one condition is a defect.

    Checked per week AND per writer. Your application and a lab script run
    in the same week are two systems with two sets of conditions, and that
    is not a second spelling of anything.
    """
    by_week: dict[tuple[int, str], set[frozenset]] = {}
    for t in TRACES:
        settings = (t.get("conditions", {}).get("settings") or {})
        keys = frozenset(k for k in settings if k != "replay")
        by_week.setdefault((t["week"], source_of(t)), set()).add(keys)
    for (week, source), shapes in by_week.items():
        assert len(shapes) <= 1, (
            f"week {week} ({source}) records its conditions under more than "
            f"one set of keys: {sorted(tuple(sorted(s)) for s in shapes)}")


def test_failures_flag_themselves():
    """Predictability floor. A failure that looks like a success cannot be
    routed by anything downstream, so a system where most of them are
    invisible is not ready for a gate."""
    dims = {d.name: d for d in report(TRACES)}
    value = dims["predictability"].value
    if value is None:
        pytest.skip("no failed runs recorded")
    assert value >= 0.5, (
        f"only {value:.0%} of failed runs flagged themselves. "
        f"{dims['predictability'].detail}")


def test_goldset_cases_are_unique():
    cases = load_goldset()
    ids = [c["case_id"] for c in cases]
    assert len(ids) == len(set(ids)), "duplicate case_id in the gold set"


def test_goldset_grew_with_the_project():
    """The gold set is the project's memory. A flat one means nobody added
    the cases their own week discovered."""
    weeks = {c.get("week_added") for c in load_goldset()}
    assert len(weeks) >= 3, f"gold set only has cases from weeks {weeks}"


# --------------------------------------------------------------------------
# TODO 5. The judged gates, marked so they can be skipped.
# --------------------------------------------------------------------------

@pytest.mark.judged
def test_judge_agrees_with_human_labels():
    """TODO 5a. The gate that licenses every other judged number.

    Load the recorded judgments, validate them against the labels, and
    assert the agreement rate clears a bar you can defend. Skip, do not
    fail, when no judgments have been recorded yet.

    An unvalidated judge is not a control. If this gate fails, no judged
    metric anywhere in your report means anything, which is why it is a
    test and not a paragraph in a README.
    """
    judgments = J.load_recorded()
    if not judgments:
        pytest.skip("no recorded judgments yet")

    missing = {case.case_id for case in J.LABELS} - judgments.keys()
    assert not missing, f"missing judgments for {sorted(missing)}"
    agreement = J.validate(judgments)
    assert agreement.rate >= 0.90, (
        f"judge agrees with only {agreement.agreed}/{agreement.n} human labels"
    )


@pytest.mark.judged
def test_judge_makes_no_false_passes():
    """TODO 5b. The asymmetric gate.

    A false fail costs a human's attention. A false pass means your gate
    went green on an invented answer. Forbid only the second, and say in
    one comment why you are not forbidding both.
    """
    judgments = J.load_recorded()
    if not judgments:
        pytest.skip("no recorded judgments yet")

    false_passes = J.validate(judgments).confusion()["false_pass"]
    # A false pass can send invented advice to a resident. A false fail gets reviewed.
    assert false_passes == 0, f"judge incorrectly passed {false_passes} human-failed answers"


@pytest.mark.judged
def test_threshold_is_not_on_a_cliff():
    """TODO 5c. Would a small change to the threshold change the verdicts?

    Compute agreement at THRESHOLD and at plus and minus 0.05, and assert
    they are close. If nudging the threshold moves agreement, the number you
    are about to report is an artefact of a library default that nobody
    chose, and you should find that out now rather than in week 12.
    """
    judgments = J.load_recorded()
    if not judgments:
        pytest.skip("no recorded judgments yet")

    baseline = J.validate(judgments).rate
    for threshold in (J.THRESHOLD - 0.05, J.THRESHOLD + 0.05):
        agreement = J.validate(judgments, threshold)
        assert abs(agreement.rate - baseline) <= 0.05, (
            f"agreement changed from {baseline:.0%} to {agreement.rate:.0%} "
            f"when threshold moved from {J.THRESHOLD:.2f} to {threshold:.2f}"
        )
