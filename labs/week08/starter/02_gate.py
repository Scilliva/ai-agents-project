"""Block 3. The gate, and what the state will not tell you. TODO 7.

Run it as TWO separate invocations. That is the whole exercise: if the pause
only survives inside one script, it is a session variable with extra steps.

    python 02_gate.py start
    python 02_gate.py resume approve      # or reject, or edit

The written answer is at the bottom, and the second half of it is the part
that is not on any slide.
"""

from __future__ import annotations

import sys
from pathlib import Path

from faults import FaultPlan
from graph import build, initial
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from project.trace import repo_root, write_json

DB = repo_root() / "artifacts" / "week08_runs.sqlite"
CASE = "RB-2026-0042"


def show(graph, cfg) -> None:
    snap = graph.get_state(cfg)
    print(f"    next node:     {snap.next}")
    print(f"    side effects:  {snap.values.get('side_effects')}")
    print(f"    events:        {snap.values.get('events')}")


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "start"
    verdict = sys.argv[2] if len(sys.argv) > 2 else "approve"
    cfg = {"configurable": {"thread_id": CASE}}
    plan = FaultPlan.parse("")          # no faults, the gate is the subject

    DB.parent.mkdir(parents=True, exist_ok=True)
    if mode == "start":
        DB.unlink(missing_ok=True)

    with SqliteSaver.from_conn_string(str(DB)) as saver:
        graph = build(plan, saver)

        if mode == "start":
            out = graph.invoke(initial(CASE, "parking vignette"), cfg)
            payload = out["__interrupt__"][0].value
            print("  the run has PAUSED at the gate\n")
            print(f"    action:    {payload['action']}")
            print(f"    arguments: {payload['arguments']}")
            print(f"    evidence:  {payload['evidence']}")
            print(f"    degraded:  {payload['degraded']}")
            show(graph, cfg)
            print("\n  This process can now exit, or be killed. Then run:")
            print("    python 02_gate.py resume approve")
            return 0

        before = graph.get_state(cfg)
        if not before.next:
            raise SystemExit("Nothing is paused. Run `start` first.")
        print(f"  resuming a run this process did not create")
        print(f"    it was paused before: {before.next}\n")

        resume = {"verdict": verdict, "by": "a.muller"}
        if verdict == "edit":
            # The approver's most common response is neither approve nor
            # reject: it is approve with one field changed. A gate with no
            # edit path throws away correct work and trains the approver to
            # approve rather than to correct.
            resume["arguments"] = {"fee": {"fee_eur": 55.0, "period": "year"}}

        out = graph.invoke(Command(resume=resume), cfg)
        print(f"    submitted: {out.get('submitted')}")
        print(f"    decision:  {out.get('decision')}")
        print(f"    fee now:   {out.get('fee')}")
        show(graph, cfg)

        record = {"case_id": CASE, "verdict": verdict,
                  "by": "a.muller", "submitted": out.get("submitted"),
                  "decision": out.get("decision"),
                  "arguments": out.get("fee"),
                  "evidence": out.get("passages"),
                  "events": out.get("events")}
        write_json("artifacts/week08_approval.json", record)
        print("\n  decision record written to artifacts/week08_approval.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
