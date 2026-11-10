"""Stage: the classifier and the policy layer. Replaced in week 3.

Until you wire yours in, there is no router: every message goes down one
path, the answer path, which is week 3's monolith control. The policy layer
records that it was a stub rather than inventing a route.

To replace it, copy your `labs/week03/starter/router.py` over this file and
change its one sibling import to a relative one:

    from routes import ROUTES, SPECIALISTS, SYSTEM_ROUTER
    from .routes import ROUTES, SPECIALISTS, SYSTEM_ROUTER

Keep these names and signatures, because `pipeline.py` calls them:

    Decision, Routed
    classify(client, text, model=SMALL.name, temperature=0.0)
        -> tuple[Decision | None, dict]
    apply_policy(decision, text) -> Routed
    respond(client, system, text, model=SMALL.name) -> tuple[str, dict]
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from project.models import SMALL

from .stub import stub

STUB_ROUTE = "info"


class Decision(BaseModel):
    route: Literal["request", "info", "status", "complaint", "other"]
    confidence: float = Field(ge=0, le=1)
    evidence: str = Field(max_length=200)


class Routed(BaseModel):
    """What the policy layer decided, and why."""

    decision: Decision
    applied_route: str
    policy_fired: str | None = None
    evidence_ok: bool = True


@stub(week=3, does="no classifier: returns no decision")
def classify(client, text: str, model: str = SMALL.name,
             temperature: float = 0.0) -> tuple[Decision | None, dict]:
    return None, {"seconds": 0.0, "prompt_tokens": 0,
                  "completion_tokens": 0, "raw": ""}


@stub(week=3, does="pass-through: every message takes the answer path")
def apply_policy(decision: Decision | None, text: str) -> Routed:
    return Routed(decision=Decision(route=STUB_ROUTE, confidence=0.0,
                                    evidence=""),
                  applied_route=STUB_ROUTE,
                  policy_fired="stub: no router, one path for everything",
                  evidence_ok=False)


@stub(week=3, does="refuses: no specialist prompts yet")
def respond(client, system: str, text: str,
            model: str = SMALL.name) -> tuple[str, dict]:
    return ("This kind of message cannot be handled yet. Please telephone "
            "the help desk on 4796-2222."), {"seconds": 0.0,
                                             "prompt_tokens": 0,
                                             "completion_tokens": 0}
