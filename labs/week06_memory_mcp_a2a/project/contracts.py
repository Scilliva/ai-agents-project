"""The contracts that cross week boundaries.

This is the narrow interface that makes fourteen practical sessions one
system. Everything else in a given week is that week's business. Anything
in this file is read by a later week, so changing it breaks something
downstream, and `project.verify` is what tells you before your classmate
does.

Three rules that the whole semester leans on.

One, a number without its conditions is not evidence. That is why
`Conditions` is required on every trace rather than optional. You cannot
write a run to disk without saying which model produced it, at what
temperature, on what date.

Two, the shape is small and the extension slot is explicit. The core fields
never change. Anything week specific goes in `notes`, which is a free
dictionary. Resist the urge to add a field here for one week's convenience.

Three, every artifact carries `schema_version`. When this file changes, that
number changes, and `project.verify` tells you which of your files are stale
instead of failing mysteriously in week 10.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

SCHEMA_VERSION = 1

# Where each artifact lives, relative to the repository root. One home per
# fact: if you need a path, import it from here rather than retyping it.
ARTIFACT_DIR = "artifacts"
TRACES_PATH = f"{ARTIFACT_DIR}/traces.jsonl"
GOLDSET_PATH = f"{ARTIFACT_DIR}/goldset.json"
FINDINGS_PATH = f"{ARTIFACT_DIR}/findings.json"
GUARD_LOG_PATH = f"{ARTIFACT_DIR}/guard_events.jsonl"


# --------------------------------------------------------------------------
# Conditions, attached to every run
# --------------------------------------------------------------------------

class Conditions(BaseModel):
    """What was true when the number was produced.

    Week 2 asks you to record the model and the date. Week 7 adds the
    chunker and the embedding model. Week 9 adds the image resolution.
    Rather than growing this class every week, the week specific parts go
    in `settings`, and the four fields that always matter are typed.
    """

    model: str = Field(description="the model that produced the run")
    temperature: float
    endpoint: str = Field(
        default="local",
        description="local, or a host name if you ever run this elsewhere")
    run_date: str = Field(description="ISO 8601 date, UTC, of the run")
    settings: dict[str, Any] = Field(
        default_factory=dict,
        description="week specific conditions: chunk size, k, resolution, "
                    "prompt version, library versions")


# --------------------------------------------------------------------------
# One step inside a run
# --------------------------------------------------------------------------

StepKind = Literal[
    "model",       # a call to the model
    "tool",        # a tool the agent invoked
    "retrieval",   # a search against the vector store or the keyword index
    "guard",       # a guardrail that ran, week 11
    "approval",    # a human gate, week 8
    "check",       # a deterministic validation, weeks 8 to 12
]


class Step(BaseModel):
    """One thing that happened, in order.

    The step list is the trajectory. Week 10 evaluates it, not just the
    final answer, which is the point MAS-Dibia chapter 10 makes: a right
    answer down a wrong path is a regression waiting to happen.
    """

    index: int = Field(ge=0)
    kind: StepKind
    name: str = Field(description="tool name, model name, or check name")
    ok: bool = True
    latency_ms: float = Field(ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    detail: dict[str, Any] = Field(
        default_factory=dict,
        description="arguments, result summary, rule that matched, verdict")


Outcome = Literal[
    "ok",         # answered, and the goal predicate is satisfied
    "refused",    # deliberately declined, which is often correct
    "degraded",   # answered partially, and said what was missing
    "blocked",    # a guardrail or a gate stopped it, week 11
    "error",      # it fell over
]


# --------------------------------------------------------------------------
# The trace, which is the spine
# --------------------------------------------------------------------------

class Trace(BaseModel):
    """One run of your system against one input.

    Every week from 4 onward appends these to `artifacts/traces.jsonl`.
    Week 10 builds the evaluation harness on them, week 11 gates on them,
    week 12 attacks the system that writes them, and week 13 cites them as
    evidence. If exactly one artifact has to survive the semester intact,
    it is this one.
    """

    schema_version: int = SCHEMA_VERSION
    trace_id: str = Field(description="unique per run, stable across reruns "
                                      "of the same case if you want to diff")
    week: int = Field(ge=1, le=14)
    case_id: str = Field(description="which gold case or task this answers")
    started_at: str = Field(description="ISO 8601 timestamp, UTC")
    conditions: Conditions
    input: str
    steps: list[Step] = Field(default_factory=list)
    output: str | None = None
    outcome: Outcome
    notes: dict[str, Any] = Field(
        default_factory=dict,
        description="week specific extension. Put anything here rather than "
                    "widening the typed fields.")

    # Derived, so that no week has to recompute them and disagree.

    @property
    def step_count(self) -> int:
        return len(self.steps)

    @property
    def total_tokens(self) -> int:
        return sum((s.input_tokens or 0) + (s.output_tokens or 0)
                   for s in self.steps)

    @property
    def total_latency_ms(self) -> float:
        return sum(s.latency_ms for s in self.steps)

    def steps_of(self, kind: StepKind) -> list[Step]:
        return [s for s in self.steps if s.kind == kind]


# --------------------------------------------------------------------------
# The gold set, grown across weeks 2, 3, 7, and 10
# --------------------------------------------------------------------------

class GoldCase(BaseModel):
    """One case your system is measured against.

    Week 2 starts it with extraction cases, week 3 adds routes, week 7 adds
    retrieval questions anchored to a document and a section, and week 10
    turns the whole thing into the golden set the harness gates on.

    `expected` is deliberately untyped. A gold answer is a string in week 2,
    a route label in week 3, and a list of sections in week 7. What matters
    is that `expected_behavior` says in words what a correct response looks
    like, because that is what a judge and a human both need.
    """

    case_id: str
    week_added: int = Field(ge=1, le=14)
    question: str
    expected: Any = None
    expected_behavior: str = Field(
        description="one sentence a colleague could grade against, for "
                    "example 'refuses, because the corpus cannot answer it'")
    slice_tags: list[str] = Field(
        default_factory=list,
        description="language, difficulty, route, or anything you want to "
                    "report per slice rather than as one average")
    must_refuse: bool = Field(
        default=False,
        description="True for cases where answering at all is the failure")


class GoldSet(BaseModel):
    schema_version: int = SCHEMA_VERSION
    cases: list[GoldCase] = Field(default_factory=list)

    def by_id(self, case_id: str) -> GoldCase | None:
        return next((c for c in self.cases if c.case_id == case_id), None)

    def tagged(self, tag: str) -> list[GoldCase]:
        return [c for c in self.cases if tag in c.slice_tags]


# --------------------------------------------------------------------------
# Week 11 and week 12 artifacts
# --------------------------------------------------------------------------

class GuardEvent(BaseModel):
    """Written every time a guardrail runs, week 11 onward."""

    schema_version: int = SCHEMA_VERSION
    trace_id: str
    guard_name: str
    placement: Literal["pre_model", "post_model", "pre_action"]
    fired: bool
    action: Literal["allow", "flag", "block", "rewrite"]
    rule: str = Field(description="which rule matched, not the input itself")
    added_ms: float = Field(ge=0)
    fail_mode_triggered: bool = Field(
        default=False,
        description="True when the guard itself errored and the declared "
                    "fail mode decided the outcome")


class Finding(BaseModel):
    """One confirmed vulnerability, week 12."""

    schema_version: int = SCHEMA_VERSION
    finding_id: str
    owasp_class: str
    severity: Literal["low", "medium", "high", "critical"]
    channel: str = Field(description="where the input entered: user input, "
                                     "retrieved passage, tool result, image")
    blast_radius: str = Field(description="what it reached, changed, or "
                                          "disclosed, concretely")
    reproduction: str = Field(description="steps another group can follow "
                                          "from a clean checkout")
    mitigation: str | None = None
    regression_test: str | None = Field(
        default=None,
        description="the test id that fails when the mitigation is removed. "
                    "A finding without one is not closed.")
    accepted_residual: bool = False
