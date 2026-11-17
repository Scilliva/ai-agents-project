"""A judge, and the labels that decide whether you are allowed to use it.

The order in this file is the argument. The hand labels come first, because
a judge you have not validated is not a measurement, it is a second opinion
from something with the same blind spot as the thing it is judging.

Measured on this stack before the session was written: the judge is stable
(five identical scores on one borderline case) and it discriminates (1.00,
0.50, 0.40, 0.00, 0.00 across five). So the question this session asks is
not "does it flake". It is "where is it wrong, and what does it cost".
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

MODEL = "qwen3:4b-instruct"
ENDPOINT = "http://127.0.0.1:11434"
THRESHOLD = 0.5

CRITERIA = (
    "Does the actual output answer the input using ONLY facts that appear in "
    "the expected output? Penalise any invented fee, deadline, office name, "
    "or document name. An answer that is correct but incomplete is better "
    "than an answer that is complete and partly invented."
)


# --------------------------------------------------------------------------
# The labels. Written by a human, before any judge ran, and that ordering is
# not decoration: a label written after seeing the score is not a label.
# --------------------------------------------------------------------------

@dataclass
class Labelled:
    case_id: str
    question: str
    expected: str
    actual: str
    human: str            # "pass" or "fail"
    why: str              # why a human said so, in a few words


VIGNETTE = ("The residential parking vignette costs 60 EUR per year and is "
            "applied for at the Bierger-Center with proof of residence.")
BINS = ("Residual waste is collected on Tuesdays. Bulky waste is collected "
        "on the first Saturday of the month, by appointment.")

LABELS: list[Labelled] = [
    # Four that any reasonable person agrees on. They are here as a control:
    # a judge that gets these wrong is not worth validating further.
    Labelled("L-01", "How much is the vignette and where do I apply?",
             VIGNETTE, VIGNETTE, "pass", "it is the expected answer"),
    Labelled("L-02", "How much is the vignette and where do I apply?",
             VIGNETTE,
             "The vignette costs 85 EUR per year and is applied for at the "
             "Bierger-Center with proof of residence.",
             "fail", "invented fee, 85 for 60"),
    Labelled("L-03", "How much is the vignette and where do I apply?",
             VIGNETTE, "The library is open on Saturday mornings.",
             "fail", "does not answer the question"),
    Labelled("L-04", "When is bulky waste collected?", BINS,
             "Bulky waste is collected on the first Saturday of the month, "
             "by appointment.", "pass", "exactly right"),

    # Eight that are genuinely arguable. This is where a judge earns or
    # loses its place, and where you should expect to disagree with it.
    Labelled("L-05", "How much is the vignette and where do I apply?",
             VIGNETTE, "The vignette costs 60 EUR per year.",
             "pass", "correct, incomplete, invents nothing"),
    Labelled("L-06", "How much is the vignette and where do I apply?",
             VIGNETTE,
             "The vignette costs 60 EUR per year and you apply online "
             "through the citizen portal.",
             "fail", "right fee, invented channel"),
    Labelled("L-07", "How much is the vignette and where do I apply?",
             VIGNETTE, "I do not have information about the vignette.",
             "fail", "honest, but it did not answer"),
    Labelled("L-08", "How much is the vignette and where do I apply?",
             VIGNETTE,
             "It costs sixty euros a year. Bring proof of residence to the "
             "Bierger-Center.",
             "pass", "same facts, different words and a spelled number"),
    Labelled("L-09", "When is bulky waste collected?", BINS,
             "Bulky waste is collected on the first Saturday of the month.",
             "pass", "true, drops the appointment requirement"),
    Labelled("L-10", "When is bulky waste collected?", BINS,
             "Waste is collected on Tuesdays.",
             "fail", "answers about the wrong waste stream"),
    Labelled("L-11", "When is bulky waste collected?", BINS,
             "Bulky waste is collected on the first Saturday of the month. "
             "Please book at least 48 hours in advance.",
             "fail", "the 48 hours is invented"),
    Labelled("L-12", "How much is the vignette and where do I apply?",
             VIGNETTE,
             "The vignette costs 60 EUR per year and is applied for at the "
             "Bierger-Center. You will need proof of residence, and there "
             "may be a waiting list.",
             "fail", "mostly right, then invents a waiting list"),
]


@dataclass
class Judgment:
    case_id: str
    score: float
    verdict: str
    reason: str
    seconds: float


@dataclass
class Agreement:
    rows: list[dict] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.rows)

    @property
    def agreed(self) -> int:
        return sum(1 for r in self.rows if r["human"] == r["judge"])

    @property
    def rate(self) -> float:
        return self.agreed / self.n if self.n else 0.0

    def confusion(self) -> dict[str, int]:
        """The two mistakes are not equally bad, so they are counted apart.

        false_pass  the judge passed something a human failed. This is the
                    dangerous one: your gate is green and the answer was
                    invented.
        false_fail  the judge failed something a human passed. Costs a
                    human's attention, and erodes trust in the gate.
        """
        out = {"true_pass": 0, "true_fail": 0, "false_pass": 0,
               "false_fail": 0}
        for r in self.rows:
            h, j = r["human"], r["judge"]
            if h == j:
                out["true_pass" if h == "pass" else "true_fail"] += 1
            else:
                out["false_pass" if j == "pass" else "false_fail"] += 1
        return out


# --------------------------------------------------------------------------
# TODO 3, answered. The judge.
# --------------------------------------------------------------------------

def build_metric():
    """TODO 3a. A GEval metric scoring CRITERIA against the local model.

    Use `deepeval.metrics.GEval` with `deepeval.models.OllamaModel`, MODEL,
    ENDPOINT, THRESHOLD, and `async_mode=False`. Its evaluation_params want
    INPUT, ACTUAL_OUTPUT, and EXPECTED_OUTPUT from
    `deepeval.test_case.SingleTurnParams`.

    Import inside the function, not at module scope, so that block 1 still
    runs for somebody who has not installed DeepEval yet. Block 1 needs no
    model at all and should not be blocked by a dependency it never uses.
    """
    raise NotImplementedError("TODO 3a: build_metric")


def judge_one(metric, case: Labelled) -> Judgment:
    """TODO 3b. Score one labelled case and time it.

    Build an `LLMTestCase` from the case, call `metric.measure`, and return
    a Judgment carrying the score, the reason, and the wall clock. Record
    the seconds even though it feels irrelevant: block 2 ends by comparing
    the cost of a judged case against the cost of a deterministic check, and
    you cannot make that argument without the number.
    """
    raise NotImplementedError("TODO 3b: judge_one")


# --------------------------------------------------------------------------
# TODO 4, answered. Validation, which is the part people skip.
# --------------------------------------------------------------------------

def validate(judgments: dict[str, Judgment],
             threshold: float | None = None) -> Agreement:
    """TODO 4. Compare the judge against the human labels, case by case.

    Return an Agreement whose rows carry the case id, the human verdict, the
    judge verdict, the score, and both reasons.

    One trap, and it is the point of the exercise. RECOMPUTE the judge
    verdict from the score and the threshold. Do not read `Judgment.verdict`
    back from the recording: that value was frozen at whatever threshold was
    in force when the call was made, so a validator that trusts it silently
    reports on an old threshold and cannot detect a bad one. The score is
    the measurement. The verdict is a decision about the score, and the
    decision belongs to whoever is asking.

    You can check you got this right: `02_judge.py` sweeps the threshold,
    and if your validate ignores it, every row of that sweep will be
    identical.
    """
    raise NotImplementedError("TODO 4: validate")


def fixture_path() -> Path:
    here = Path(__file__).resolve()
    for base in (here.parent, here.parent.parent, Path.cwd(), Path.cwd().parent):
        p = base / "fixtures" / "judgments.json"
        if p.exists():
            return p
    return here.parent.parent / "fixtures" / "judgments.json"


def load_recorded() -> dict[str, Judgment]:
    p = fixture_path()
    if not p.exists():
        return {}
    return {k: Judgment(**v) for k, v in json.loads(p.read_text()).items()}


def save_recorded(judgments: dict[str, Judgment]) -> None:
    p = fixture_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({k: vars(v) for k, v in judgments.items()},
                            indent=1) + "\n")
