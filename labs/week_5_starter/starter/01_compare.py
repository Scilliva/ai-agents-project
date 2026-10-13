"""Blocks 1 to 3. Three architectures on the same task. TODO 6 and 7.

    python 01_compare.py --replay
    python 01_compare.py --runs 3

Same task, same repository, same verifier, one variable: how much
architecture sits between the model and the edit.

  A  baseline          free-form tool loop, the week 4 shape on Pydantic AI
  B  planner + fixer   plan, validate the plan, then one structured proposal
  C  B + reviewer      the same, with a second agent gating the proposal

The written answers are at the bottom.
"""

from __future__ import annotations

import argparse
import asyncio
import time

from agents import Verdict, baseline, propose, reviewer, validate_plan
from repo import Work, apply_fix, diff_summary, run_tests

from project.contracts import GoldCase, GoldSet
from project.fixtures import load_or_reference
from project.trace import TraceRecorder, local_conditions, write_json

LAB = "week05_planner_multi_agent"

TASK = ("A test is failing. The off-peak discount is meant to apply to "
        "bookings that start at 20:00 or later, but a booking starting "
        "exactly at 20:00 does not receive it. Fix the bug. Do not change "
        "any test file.")


def record(arch: str, run_index: int, outcome: str, **notes) -> None:
    rec = TraceRecorder(
        week=5, case_id=f"{arch}-run{run_index}",
        conditions=local_conditions("qwen2.5:7b", temperature=0.0,
                                    architecture=arch),
        user_input=TASK)
    with rec.step("check", "run_tests") as span:
        span.detail(**{k: str(v)[:200] for k, v in notes.items()})
    rec.finish(output=str(notes.get("fix", "")), outcome=outcome, **{
        k: str(v)[:300] for k, v in notes.items()})


async def run_baseline(index: int) -> dict:
    work = Work.fresh()
    t0 = time.perf_counter()
    calls = 0
    try:
        r = await baseline.run(TASK, deps=work)
        calls = sum(1 for m in r.all_messages() for p in m.parts
                    if getattr(p, "tool_name", None))
        tokens = r.usage.total_tokens or 0
    except Exception as exc:                                  # noqa: BLE001
        tokens = 0
        print(f"    baseline run {index} raised {type(exc).__name__}")
    green = run_tests(work).passed
    row = {"architecture": "A baseline", "green": green,
           "tool_calls": calls, "tokens": tokens,
           "seconds": round(time.perf_counter() - t0, 1)}
    record("A-baseline", index, "ok" if green else "error", **row)
    work.cleanup()
    return row


async def run_planned(index: int, with_reviewer: bool) -> dict:
    work = Work.fresh()
    t0 = time.perf_counter()
    out = await propose(work, TASK, use_plan=True)
    fix = out["fix"]

    verdict = None
    if with_reviewer:
        diff = diff_summary(work, fix.path, fix.old_line, fix.new_line)
        failing = run_tests(work).output
        r = await reviewer.run(f"Proposed change:\n{diff}\n\n"
                               f"Failing test output:\n{failing}")
        verdict = r.output
        out["tokens"] += r.usage.total_tokens or 0

    applied = "not attempted"
    if verdict is None or verdict.decision == "approve":
        applied = apply_fix(work, fix.path, fix.old_line, fix.new_line)
    green = run_tests(work).passed

    row = {"architecture": "C planner+reviewer" if with_reviewer
           else "B planner", "green": green,
           "plan_ok": out["plan_ok"], "plan_problems": out["plan_problems"],
           "applied": applied,
           "verdict": verdict.decision if verdict else None,
           "verdict_reason": verdict.reason if verdict else None,
           "fix": f"{fix.path}: {fix.old_line.strip()} -> "
                  f"{fix.new_line.strip()}",
           "tokens": out["tokens"],
           "seconds": round(time.perf_counter() - t0, 1)}
    record(row["architecture"], index, "ok" if green else "error", **row)
    work.cleanup()
    return row


async def main_async(runs: int) -> list[dict]:
    rows = []
    for i in range(1, runs + 1):
        rows.append(await run_baseline(i))
        rows.append(await run_planned(i, with_reviewer=False))
        rows.append(await run_planned(i, with_reviewer=True))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--replay", action="store_true",
                    help="read the recorded reference runs instead of calling")
    args = ap.parse_args()

    if args.replay:
        from pathlib import Path
        import json
        from project.fixtures import find_fixture
        path = find_fixture("reference_runs.json", __file__, lab=LAB)
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        print(f"replay: {payload['meta']['runs']} runs per architecture, "
              f"model {payload['meta']['model']}, "
              f"recorded {payload['meta']['recorded_at']}\n")
        rows = payload["rows"]
    else:
        rows = asyncio.run(main_async(args.runs))

    by_arch: dict[str, list[dict]] = {}
    for row in rows:
        by_arch.setdefault(row["architecture"], []).append(row)

    print(f"{'architecture':<22}{'green':>8}{'tokens':>10}{'seconds':>9}")
    print("-" * 50)
    for arch, group in by_arch.items():
        green = sum(bool(r["green"]) for r in group)
        print(f"{arch:<22}{green:>4}/{len(group):<3}"
              f"{sum(r['tokens'] for r in group) // len(group):>10}"
              f"{sum(r['seconds'] for r in group) / len(group):>9.1f}")

    print("\nwhat each architecture proposed:")
    for row in rows:
        if row.get("fix"):
            flag = "green" if row["green"] else "RED  "
            v = f"  reviewer={row['verdict']}" if row.get("verdict") else ""
            print(f"  [{flag}] {row['architecture']:<20} {row['fix'][:64]}{v}")

    write_json("artifacts/week05_architectures.json", {"rows": rows})

    # TODO 7. Two cases enter the gold set.
    #
    #   The first is the fix you expect. The second is the one that matters:
    #   a change that makes the failing test pass and is still wrong. Write
    #   its expected_behavior as a prohibition rather than an instruction,
    #   and say why it is wrong. Week 10 will ask a judge to grade against
    #   that sentence.
    existing, source = load_or_reference("goldset.json", lab=LAB)
    print(f"\ngold set loaded from: {source}")
    goldset = GoldSet.model_validate(existing)
    already = {c.case_id for c in goldset.cases}
    for case_id, question, behavior, tags in [
        ("W5-bugfix", TASK,
         "changes the comparison in is_off_peak from > to >=, so that a "
         "booking at exactly 20:00 gets the discount, and the full suite "
         "goes green",
         ["task:coding", "verifier:tests"]),
        ("W5-constant-trap", TASK,
         "does NOT fix this by lowering OFF_PEAK_FROM_HOUR from 20 to 19. "
         "That makes the failing test pass and is wrong, because it also "
         "gives the discount to bookings at 19:00.",
         ["task:coding", "plausible-wrong-fix"]),
    ]:
        if case_id in already:
            continue
        goldset.cases.append(GoldCase(
            case_id=case_id, week_added=5, question=question,
            expected={"file": "discounts.py", "operator": ">="},
            expected_behavior=behavior, slice_tags=tags))
    write_json("artifacts/goldset.json", goldset)
    print(f"gold set now holds {len(goldset.cases)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
