"""Does a LangGraph interrupt survive a process kill?

Week 8's demonstration is: start a run, hit a human approval gate, kill the
process, and resume from a SECOND process against the same thread id. If the
pause only survives inside one script, it is a session variable with extra
steps and the session teaches nothing.

Run as two separate invocations, which is the whole point:

    python probe_week08.py start
    python probe_week08.py resume approve
"""

import sys
from pathlib import Path
from typing import Annotated, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

DB = Path("/tmp/w08_probe.sqlite")
THREAD = "case-0001"


class CaseState(TypedDict):
    subject: str
    draft: str
    submitted: bool
    decision: str
    side_effects: Annotated[list[str], lambda a, b: a + b]


def prepare(state: CaseState) -> dict:
    return {"draft": f"ticket for {state['subject']}",
            "side_effects": ["prepared"]}


def submit(state: CaseState) -> dict:
    # The claim under test: everything above the interrupt runs AGAIN on
    # resume, because the node re-executes from its first line.
    print("      [side effect ABOVE the interrupt executed]")
    _above = {"side_effects": ["WROTE_ABOVE_INTERRUPT"]}
    decision = interrupt({"action": "submit_case",
                          "arguments": {"draft": state["draft"]},
                          "reason": "irreversible and externally visible"})
    if decision.get("verdict") != "approve":
        return {"submitted": False, "decision": decision.get("verdict", "?"),
                "side_effects": _above["side_effects"] + ["refused"]}
    return {"submitted": True, "decision": "approve",
            "side_effects": _above["side_effects"] + ["SUBMITTED"]}


def build(saver):
    g = StateGraph(CaseState)
    g.add_node("prepare", prepare)
    g.add_node("submit", submit)
    g.add_edge(START, "prepare")
    g.add_edge("prepare", "submit")
    g.add_edge("submit", END)
    return g.compile(checkpointer=saver)


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "start"
    cfg = {"configurable": {"thread_id": THREAD}}

    with SqliteSaver.from_conn_string(str(DB)) as saver:
        graph = build(saver)
        if mode == "start":
            DB.unlink(missing_ok=True)
        with SqliteSaver.from_conn_string(str(DB)) as saver2:
            graph = build(saver2)
            if mode == "start":
                out = graph.invoke({"subject": "A. Muller", "draft": "",
                                    "submitted": False, "decision": "",
                                    "side_effects": []}, cfg)
                print("  run paused. state now:")
                print(f"    __interrupt__ present: {'__interrupt__' in out}")
                if "__interrupt__" in out:
                    payload = out["__interrupt__"][0].value
                    print(f"    payload action: {payload.get('action')}")
                    print(f"    payload reason: {payload.get('reason')}")
                snap = graph.get_state(cfg)
                print(f"    next node: {snap.next}")
                print(f"    side effects so far: "
                      f"{snap.values.get('side_effects')}")
                print("\n  now run:  python probe_week08.py resume approve")
            else:
                verdict = sys.argv[2] if len(sys.argv) > 2 else "approve"
                before = graph.get_state(cfg)
                print(f"  resuming a run this process did not create")
                print(f"    next node was: {before.next}")
                out = graph.invoke(
                    Command(resume={"verdict": verdict, "by": "a.muller"}),
                    cfg)
                print(f"    submitted: {out.get('submitted')}")
                print(f"    decision:  {out.get('decision')}")
                print(f"    side effects: {out.get('side_effects')}")
                dupes = [e for e in out.get("side_effects", [])
                         if out["side_effects"].count(e) > 1]
                print(f"    duplicated side effects: {sorted(set(dupes)) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
