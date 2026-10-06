"""Blocks 1 and 2. Run the agent, score it, record it. TODO 7.

    python 01_run.py --replay          # the recording, instant, no model
    python 01_run.py                   # your own machine, about 45 seconds
    python 01_run.py --model qwen3:4b-instruct   # the other text model

The recording holds every call, on both models, plus a no-tool baseline.
Develop against it, then run live.

It contains real failures, unedited. The reference run passes 5 of 10, and
the five failures are the session. If your scorer reports 10 of 10, your
scorer does nothing.
"""

from __future__ import annotations

import argparse

from agent import SYSTEM, run_task
from scoring import report, score_all
from tasks import TASKS

from project.contracts import GoldCase, GoldSet
from project.fixtures import ReplayClient, load_or_reference
from project.models import BASE_URL, API_KEY, LARGE
from project.trace import write_json

LAB = "week04_react_tool_use"


def get_client(replay: bool):
    if replay:
        client = ReplayClient.from_lab(LAB)
        print(f"replay: {client.describe()}\n")
        return client
    from openai import OpenAI
    return OpenAI(base_url=BASE_URL, api_key=API_KEY)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--model", default=LARGE.name)
    ap.add_argument("--max-steps", type=int, default=6)
    ap.add_argument("--no-tools", action="store_true",
                    help="the baseline: answer with no tools at all")
    args = ap.parse_args()

    client = get_client(args.replay)

    runs = [run_task(client, t, model=args.model, max_steps=args.max_steps)
            for t in TASKS]
    board = score_all(TASKS, runs)
    print(report(board, runs))

    print("\nper task:")
    for task, run in zip(TASKS, runs):
        mark = "ok " if next(r.passed for r in board.results
                             if r.task_id == task.id) else "FAIL"
        print(f"  [{mark}] {task.id}  steps {run.steps}  "
              f"{run.seconds:5.1f}s  tools={run.tool_calls}")

    write_json("artifacts/week04_agent.json", {
        "model": args.model, "max_steps": args.max_steps,
        "passed": board.passed, "total": board.total,
        "failed": board.failed_ids,
        "tool_abuse": board.tool_abuse, "invented": board.invented,
        "injection_seen": board.injection_seen,
        "injection_followed": board.injection_followed,
        "capped": board.capped,
        "steps": [r.steps for r in runs],
        "tokens": sum(r.tokens for r in runs),
    })

    # TODO 7. Add the ten agent tasks to the gold set.
    #
    #   Load it with load_or_reference, as week 3 did, and print which copy
    #   you got. Append one GoldCase per task with week_added=4, the gold
    #   strings and expected_tools in `expected`, and slice tags for the
    #   language, "needs-no-tool" where expected_tools is empty, and
    #   "injection" where the task carries a forbidden marker.
    #
    #   One field is new and it matters. Set `must_refuse=True` on the task
    #   whose forbidden_regex is set. Until now every gold case had an
    #   answer; this one has none, and answering confidently is the failure
    #   rather than the success. Week 10's harness needs that distinction
    #   written in the data rather than remembered by whoever wrote it.
    existing, source = load_or_reference("goldset.json", lab=LAB)
    print(f"\ngold set loaded from: {source}")
    goldset = GoldSet.model_validate(existing)
    already = {c.case_id for c in goldset.cases}

    for task in TASKS:
        if task.id in already:
            continue
        tags = [f"lang:{task.lang}", "task:agent"]
        if not task.expected_tools:
            tags.append("needs-no-tool")
        if task.forbidden:
            tags.append("injection")
        goldset.cases.append(GoldCase(
            case_id=task.id, week_added=4, question=task.question,
            expected={"gold_all": list(task.gold_all),
                      "gold_any": list(task.gold_any),
                      "expected_tools": list(task.expected_tools)},
            expected_behavior=task.why or "answers from the handbook",
            slice_tags=tags,
            must_refuse=bool(task.forbidden_regex)))

    write_json("artifacts/goldset.json", goldset)
    print(f"gold set now holds {len(goldset.cases)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
