"""The application's approval gate for irreversible submissions.

Attended runs pause in LangGraph, show the exact payload to a person, and
resume the same checkpoint with their approve, reject, or edit decision.
Unattended runs fail closed immediately with a timeout decision.
"""

from __future__ import annotations

import json
import uuid
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from project.trace import repo_root


class _ApprovalState(TypedDict):
    payload: dict
    decision: dict


def _pause_for_decision(state: _ApprovalState) -> dict:
    """Pause before returning a human decision; do no writes before pause."""
    decision = interrupt(state["payload"])
    return {"decision": decision}


def _timeout(payload: dict) -> dict:
    return {
        "verdict": "timeout",
        "by": "timeout",
        "arguments": payload.get("arguments", {}),
    }


def _ask_human(payload: dict) -> dict:
    print("\nApproval required")
    print(f"Action: {payload.get('action')}")
    print(f"Case: {payload.get('case_id')}")
    print(f"Arguments: {json.dumps(payload.get('arguments', {}), ensure_ascii=False)}")
    print(f"Evidence: {json.dumps(payload.get('evidence', []), ensure_ascii=False)}")
    print(f"Degraded: {payload.get('degraded', False)}")

    while True:
        try:
            choice = input("Decision [approve/reject/edit]: ").strip().lower()
        except EOFError:
            return _timeout(payload)
        if choice in {"approve", "reject", "edit"}:
            break
        print("Enter approve, reject, or edit.")

    try:
        approver = input("Approver name or ID: ").strip() or "anonymous"
    except EOFError:
        return _timeout(payload)

    decision = {"verdict": choice, "by": approver}
    if choice == "edit":
        try:
            edited = json.loads(input("Edited arguments as JSON object: "))
        except (EOFError, json.JSONDecodeError):
            return {"verdict": "reject", "by": approver,
                    "arguments": payload.get("arguments", {})}
        if not isinstance(edited, dict):
            return {"verdict": "reject", "by": approver,
                    "arguments": payload.get("arguments", {})}
        decision["arguments"] = edited
    else:
        decision["arguments"] = payload.get("arguments", {})
    return decision


def request_approval(payload: dict, unattended: bool = False) -> dict:
    """Ask before submission; unattended requests time out without waiting."""
    if unattended:
        return _timeout(payload)

    builder = StateGraph(_ApprovalState)
    builder.add_node("approval", _pause_for_decision)
    builder.add_edge(START, "approval")
    builder.add_edge("approval", END)

    checkpoint = repo_root() / "artifacts" / "app_approvals.sqlite"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    config = {"configurable": {"thread_id": uuid.uuid4().hex}}

    with SqliteSaver.from_conn_string(str(checkpoint)) as saver:
        approval_graph = builder.compile(checkpointer=saver)
        paused = approval_graph.invoke(
            {"payload": payload, "decision": {}}, config)
        if not paused.get("__interrupt__"):
            return paused.get("decision") or _timeout(payload)

        human_decision = _ask_human(payload)
        completed = approval_graph.invoke(
            Command(resume=human_decision), config)
        return completed.get("decision") or _timeout(payload)
