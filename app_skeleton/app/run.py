"""Run the application. One request, or the whole gold set.

From the root of your repository:

    python -m app.run "My heating has been broken for three weeks."
    python -m app.run --subject "A. Muller" "When is my bin collected?"
    python -m app.run --route request "The badge reader is broken."
    python -m app.run --image labs/week09/images/INV-001.png "Post this."
    python -m app.run --batch                 # every gold case, unattended
    python -m app.run --batch --repeat 2      # twice, for consistency
    python -m app.run --stages                # which stages are still stubs

Every request appends exactly one trace to `artifacts/traces.jsonl`, and the
command reads it back before it reports success. So this is the one command
that proves the application still runs end to end: if it exits 0, a valid
trace was written. Run `python -m project.verify` after it, as always.

The exit code is 1 when a run ended in "error", and 0 for every other
outcome, because a refusal from a stub is the stub working as designed.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from project.contracts import GoldSet
from project.fixtures import load_or_reference
from project.trace import read_traces

from . import pipeline

# Where a missing gold set falls back to, newest first. Each of these labs
# ships a reference copy in fixtures/reference/.
REFERENCE_LABS = ("week08_robustness_hitl", "week07_rag_pipeline",
                  "week06_memory_mcp_a2a", "week05_planner_multi_agent",
                  "week04_react_tool_use", "week03_routing_and_composition")


def print_stages() -> None:
    print(f"{'stage':<8}{'week':>5}   status")
    for name, s in pipeline.status().items():
        state = "STUB, " + s["does"] if s["stub"] else "built"
        print(f"{name:<8}{s['week']:>5}   {state}")


def load_goldset(path: str | None) -> tuple[GoldSet, str]:
    """Your own gold set, or the newest reference copy you have unpacked."""
    if path:
        return GoldSet.model_validate_json(
            Path(path).read_text(encoding="utf-8")), path
    for lab in REFERENCE_LABS:
        try:
            data, source = load_or_reference("goldset.json", lab=lab)
        except FileNotFoundError:
            continue
        return GoldSet.model_validate(data), (
            "own" if source == "own" else f"reference copy from {lab}")
    raise SystemExit(
        "No gold set found: artifacts/goldset.json is missing and no lab "
        "with a reference copy is unpacked under labs/. Pass --goldset.")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m app.run",
                                 description=__doc__.splitlines()[0])
    ap.add_argument("request", nargs="?", help="the request text")
    ap.add_argument("--subject", help="who the request is about, for memory")
    ap.add_argument("--image", help="an image that comes with the request")
    ap.add_argument("--route", choices=("request", "info", "status",
                                        "complaint", "other"),
                    help="skip the router and force this route")
    ap.add_argument("--case-id", help="the case this request answers")
    ap.add_argument("--week", type=int,
                    help="the week to record, default: the latest built stage")
    ap.add_argument("--unattended", action="store_true",
                    help="nobody answers the approval gate")
    ap.add_argument("--batch", action="store_true",
                    help="run every gold case, unattended")
    ap.add_argument("--goldset", help="a gold set file, default: your own")
    ap.add_argument("--repeat", type=int, default=1,
                    help="batch only: how many times to run each case")
    ap.add_argument("--stages", action="store_true",
                    help="list the stages and stop")
    args = ap.parse_args(argv)

    if args.stages:
        print_stages()
        return 0

    if args.batch:
        goldset, source = load_goldset(args.goldset)
        print(f"gold set: {len(goldset.cases)} cases, {source}, "
              f"run {args.repeat} time(s), unattended\n")
        traces = pipeline.run_batch(goldset.cases, repeat=args.repeat,
                                    week=args.week)
        on_disk = {t.trace_id for t in read_traces()}
        lost = [t.trace_id for t in traces if t.trace_id not in on_disk]
        counts = Counter(t.outcome for t in traces)
        print("  ".join(f"{o} {n}" for o, n in sorted(counts.items())))
        stubbed = traces[0].notes["stubbed"] if traces else []
        print(f"stubs: {', '.join(stubbed) or 'none'}")
        print(f"{len(traces)} traces appended to artifacts/traces.jsonl")
        if lost:
            print(f"FAIL: {len(lost)} traces were not read back")
            return 1
        return 1 if counts.get("error") else 0

    if not args.request:
        ap.error("give a request, or --batch, or --stages")

    trace = pipeline.handle(args.request, case_id=args.case_id,
                            subject=args.subject, image=args.image,
                            route=args.route, week=args.week,
                            unattended=args.unattended)
    print_stages()
    print()
    for step in trace.steps:
        tag = "stub" if step.detail.get("stub") else "    "
        ok = "ok " if step.ok else "ERR"
        hits = (f"   hits {step.detail['hits']}"
                if "hits" in step.detail else "")
        print(f"  {step.index:>2} {ok} {tag} {step.kind:<9} {step.name:<28}"
              f"{step.latency_ms:>8.1f} ms{hits}")
    print(f"\n{trace.output}\n")
    print(f"outcome  {trace.outcome}")
    print(f"case     {trace.case_id}   week {trace.week}   "
          f"model {trace.conditions.model}")
    if trace.notes.get("error"):
        print(f"error    {trace.notes['error']}")

    if trace.trace_id not in {t.trace_id for t in read_traces()}:
        print("FAIL: the trace was not read back from artifacts/traces.jsonl")
        return 1
    print(f"trace    {trace.trace_id}, appended to artifacts/traces.jsonl")
    return 1 if trace.outcome == "error" else 0


if __name__ == "__main__":
    sys.exit(main())
