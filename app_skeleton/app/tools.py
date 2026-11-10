"""Stage: the tools the agent may call. Replaced in week 4.

Copy your `labs/week04/starter/tools.py` and `handbook.py` into `app/`, then
change the one sibling import in `tools.py` to a relative one:

    import handbook
    from . import handbook

Keep these names, because `agent.py` imports them:

    SCHEMAS                          the tool schemas, provider shaped
    search_services(query, top_k=3) -> list[dict]
    compute(expression) -> float

Week 7 is where `search_services` can stop searching the week 4 handbook
and start calling your retriever. Whether it should is a design decision.
"""

from __future__ import annotations

from typing import Any

from .stub import stub

SCHEMAS: list[dict[str, Any]] = []
SCHEMAS_SEARCH_ONLY: list[dict[str, Any]] = []


@stub(week=4, does="refuses: finds nothing")
def search_services(query: str, top_k: int = 3) -> list[dict]:
    return []


@stub(week=4, does="refuses: raises rather than guessing a number")
def compute(expression: str) -> float:
    raise ValueError("stub: the week 4 compute tool is not wired in")


REGISTRY = {"search_services": search_services, "compute": compute}
