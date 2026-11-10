"""The pipeline as a graph, with one gated step. TODO 3 to 5.

Four nodes. Three of them execute automatically and one stops and asks a
human, and which one is a decision about consequence rather than about
confidence.
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from faults import ContractDrift, FaultPlan
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from retry import StepPolicy, call_with_policy

import tools


def append(a: list, b: list) -> list:
    return a + b


class CaseState(TypedDict):
    case_id: str
    topic: str
    passages: list[str]
    fee: dict
    draft: str
    submitted: bool
    decision: str
    degraded: bool
    missing: Annotated[list[str], append]
    events: Annotated[list[str], append]
    side_effects: Annotated[list[str], append]


SEARCH_POLICY = StepPolicy(attempts=3, base_delay=0.05, jitter=True,
                           max_elapsed=3.0, on_exhausted="degrade")
FEES_POLICY = StepPolicy(attempts=3, base_delay=0.05, jitter=True,
                         max_elapsed=3.0, on_exhausted="degrade")


def validate_fee(value) -> None:
    """TODO 4. Where contract drift is caught.

    Drift is the fault no retry fixes, because the call succeeded. The only
    thing that catches it is a check on the SHAPE of what came back, run on
    the success path. If you have no validation, a renamed field flows all
    the way to the answer and the run reports success.
    """
    raise NotImplementedError("TODO 4: validate the fee contract")


# --------------------------------------------------------------------------
# TODO 3. The nodes, each with its own policy.
# --------------------------------------------------------------------------

def gather(state: CaseState, plan: FaultPlan) -> dict:
    """TODO 3a. Search, with retries and a fallback.

    Three cases, and the middle one is the interesting one:

      the call failed after everything    -> degraded, say search is down
      the call SUCCEEDED and returned []  -> decide, and be able to defend it
      the call succeeded with passages    -> note if the fallback was used

    An empty result is not an error and it is not a success either. It is
    the tool saying it does not cover this. Treating it as a success is how
    a pipeline answers a question from nothing.

    Record what is absent in `missing` so `draft` can say it out loud, and
    append to `events` so the checkpoint has something to count.
    """
    raise NotImplementedError("TODO 3a: gather with a policy")


def price(state: CaseState, plan: FaultPlan) -> dict:
    """TODO 3b. The fee lookup, passing `validate_fee` to the policy.

    This is the step contract drift hits. Without a validator the renamed
    field flows into the answer and the run reports success.
    """
    raise NotImplementedError("TODO 3b: price with validation")


def draft(state: CaseState) -> dict:
    """TODO 5. The goal predicate, and what a partial answer says.

    A degraded answer must name what is missing IN THE TEXT THE USER READS.
    An answer that quietly omits the fee is indistinguishable from one where
    there was no fee, and the reader has no way to know which they got.

    A degrade path that returns an empty string is technically graceful and
    completely useless.
    """
    raise NotImplementedError(
        "TODO 5: assemble the answer and name what is missing")


def submit(state: CaseState) -> dict:
    """The gated step. Exactly one, chosen by consequence.

    Everything above the interrupt runs AGAIN on resume, because the node
    re-executes from its first line. Put nothing here that writes.

    And the part the state will not show you: the first execution never
    returns, so its return value is discarded while whatever it did to the
    outside world is not. A write above this line happens twice and appears
    once. `02_gate.py` demonstrates it.
    """
    decision = interrupt({
        "action": "submit_case",
        "case_id": state["case_id"],
        # The exact arguments, not a summary the model wrote. The model
        # whose judgment you are checking would also be writing the account
        # of it.
        "arguments": {"topic": state["topic"], "fee": state.get("fee", {})},
        "evidence": state.get("passages", []),
        "degraded": state.get("degraded", False),
        "missing": sorted(set(state.get("missing", []))),
    })

    verdict = decision.get("verdict")
    if verdict == "approve":
        return {"submitted": True, "decision": "approve",
                "side_effects": [f"SUBMITTED {state['case_id']}"],
                "events": [f"gate:approve:{decision.get('by', '?')}"]}
    if verdict == "edit":
        edited = decision.get("arguments", {})
        return {"submitted": True, "decision": "edit",
                "fee": edited.get("fee", state.get("fee", {})),
                "side_effects": [f"SUBMITTED {state['case_id']} (edited)"],
                "events": [f"gate:edit:{decision.get('by', '?')}"]}
    return {"submitted": False, "decision": verdict or "reject",
            "events": [f"gate:{verdict or 'reject'}:"
                       f"{decision.get('by', '?')}"]}


def build(plan: FaultPlan, saver):
    graph = StateGraph(CaseState)
    graph.add_node("gather", lambda s: gather(s, plan))
    graph.add_node("price", lambda s: price(s, plan))
    graph.add_node("draft", draft)
    graph.add_node("submit", submit)
    graph.add_edge(START, "gather")
    graph.add_edge("gather", "price")
    graph.add_edge("price", "draft")
    graph.add_edge("draft", "submit")
    graph.add_edge("submit", END)
    return graph.compile(checkpointer=saver)


def initial(case_id: str, topic: str) -> CaseState:
    return {"case_id": case_id, "topic": topic, "passages": [], "fee": {},
            "draft": "", "submitted": False, "decision": "",
            "degraded": False, "missing": [], "events": [],
            "side_effects": []}
