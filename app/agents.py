"""Stage: the planner and the reviewer. Replaced in week 5.

Week 5 builds a planner, a free plan validator, and a reviewer on Pydantic
AI, against a toy repository. The pattern transfers to this application and
the repository does not, so this is one of the two stages you write rather
than copy. Keep the shapes week 5 taught you, minus `suspect_file`, which
named a file in the toy repository:

    Plan(goal: str, steps: list[str])      flat, because nested fails
    validate_plan(plan) -> tuple[bool, list[str]]
    Verdict(decision: "approve" | "reject", reason: str)

and provide the two functions `pipeline.py` calls, plus the name of the
model your agents use, so the trace records it:

    make_plan(question: str) -> Plan
    review(question: str, answer: str, evidence: list[str]) -> Verdict | None
    MODEL_NAME: str                         for example LARGE.name

Your `validate_plan` checks steps against the tools the agent actually has
(`tools.REGISTRY`) instead of week 5's KNOWN_FILES. Your reviewer sees the
answer and the evidence and not the agent's reasoning, for the reason week 5
gave: a reviewer that inherits the reasoning inherits the mistake.

`review` returning None means "not reviewed". The stub returns None rather
than an approval, because a stub that approves everything would be a stub
claiming to have checked something.

If week 5 measured that the plain loop wins, keep all three pass-throughs
and delete all three `@stub` lines below, and say so in DECISIONS.md. A
pass-through you chose is a design. One you skipped is a stub.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from project.models import LARGE, pydantic_ai_model
from . import tools


class Plan(BaseModel):
    goal: str
    steps: list[str]


class Verdict(BaseModel):
    decision: Literal["approve", "reject"]
    reason: str = Field(max_length=200)


MODEL_NAME = LARGE.name

planner = Agent(
    pydantic_ai_model(LARGE),
    output_type=Plan,
    retries=3,
    system_prompt=(
        "You plan how the Remerbaach help-desk agent should answer one user "
        "question. You do not answer the user and you do not call tools. "
        "Return a goal and between two and six short, ordered steps. Every "
        "step must start with exactly 'tool: NAME —' followed by what the "
        "step does. NAME must be one of search_services, compute, or none. "
        "Use search_services for facts from the commune handbook, compute "
        "for arithmetic, and none when a step needs no tool. Never invent "
        "a tool. The agent has only the tools named here."
    ),
)


def make_plan(question: str) -> Plan:
    """Ask the structured planner for a short plan before the agent runs."""
    return planner.run_sync(question).output


def validate_plan(plan: Plan) -> tuple[bool, list[str]]:
    """Check plan size and every declared tool against the live registry."""
    problems: list[str] = []
    if not 2 <= len(plan.steps) <= 6:
        problems.append("Plan must have between 2 and 6 steps.")

    available = set(tools.REGISTRY)
    for index, step in enumerate(plan.steps, start=1):
        match = re.match(r"^\s*tool:\s*([A-Za-z_][A-Za-z0-9_]*|none)\b",
                         step, flags=re.IGNORECASE)
        if not match:
            problems.append(
                f"Step {index} must start with 'tool: NAME —'.")
            continue
        name = match.group(1)
        if name.lower() != "none" and name not in available:
            problems.append(
                f"Step {index} names unknown tool {name!r}; available tools: "
                f"{', '.join(sorted(available))}.")
    return not problems, problems


def review(question: str, answer: str,
           evidence: list[str]) -> Verdict | None:
    """Architecture B is planner-only, so deliberately skip a second model."""
    return None
