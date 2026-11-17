"""Block 1: read five invoices, and find out what your checks can see.

The table this prints has five columns and only one of them matters. WRONG
counts extractions that were incorrect AND passed every check, which means
the only way to find them would have been for a human to open the image.

    python 01_extract.py --replay     # the recorded run, instant
    python 01_extract.py              # live, about six minutes
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "project_spine"))

from checks import ALL_FIELDS, GROUPS, classify, run_checks, tally  # noqa: E402
from vision import (MODEL as VISION_MODEL, Fixture, VisionResult,  # noqa: E402
                    find_fixture, read_group)

from project.trace import (TraceRecorder, local_conditions,  # noqa: E402
                           write_json)

IMAGES = Path(__file__).resolve().parent.parent / "images"
DOCS = ["INV-001", "INV-002", "INV-003", "INV-004", "INV-005"]


def truth_for(doc: str) -> dict:
    data = json.loads((IMAGES / "ground_truth.json").read_text())
    for row in data["documents"]:
        if row["document_id"] == doc:
            return row
    raise KeyError(doc)


def extract_one(doc: str, variant: str, replay: Fixture | None,
                record: Fixture | None) -> tuple[dict, list[VisionResult]]:
    """Two calls, one group of three fields each."""
    fields: dict[str, str | None] = {}
    results = []
    for group, group_fields in GROUPS.items():
        res = read_group(IMAGES / f"{doc}.png", group, group_fields,
                         variant=variant, replay=replay, record=record)
        results.append(res)
        fields.update(res.fields if res.ok
                      else {f: None for f in group_fields})
    return fields, results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true",
                    help="use the recorded run instead of calling the model")
    ap.add_argument("--variant", default="clean",
                    help="a perturb.py variant, for example scale=0.4")
    args = ap.parse_args()

    replay = Fixture(find_fixture()) if args.replay else None
    if replay is not None and not replay.entries:
        print("no fixture found. Run without --replay, or fetch "
              "fixtures/vision_runs.jsonl from the lab folder.")
        return 1

    rows = []
    print(f"{'doc':<9}{'total read':>12}{'truth':>11}{'outcome':>12}"
          f"{'s':>7}  first check that fired")
    print("-" * 88)

    for doc in DOCS:
        truth = truth_for(doc)
        rec = TraceRecorder(
            week=9, case_id=doc,
            conditions=local_conditions(VISION_MODEL, temperature=0.0,
                                        variant=args.variant,
                                        replay=bool(args.replay)),
            user_input=f"read {doc}.png as {args.variant}")
        # kind="model": a vision call is a model call. The Step schema keeps
        # a closed enumeration of kinds on purpose, so week 10 can group
        # steps across every week without a mapping table.
        with rec.step("model", "extract") as span:
            fields, results = extract_one(doc, args.variant, replay, None)
            span.ok = all(r.ok for r in results)
            span.detail(calls=len(results),
                        failures=[r.failure for r in results if not r.ok])
        report = run_checks(fields)
        outcome = classify(truth, report)
        failures = [r.failure for r in results if not r.ok]
        elapsed = sum(r.elapsed_s for r in results)
        note = failures[0] if failures else (report.fired[0]
                                            if report.fired else "")
        # The five outcomes this session measures are finer grained than the
        # five the Trace contract carries, so they are mapped rather than
        # bolted on. A false alarm still answered correctly, so it is "ok"
        # in the trace and a defect in this session's own table.
        trace = rec.finish(
            output=str(report.parsed["total"]),
            outcome={"correct": "ok", "false_alarm": "ok", "caught": "degraded",
                     "WRONG": "error", "refused": "refused"}[outcome],
            verdict=outcome, checks_fired=report.fired,
            call_failures=failures)
        rows.append({"doc": doc, "outcome": outcome, "fields": fields,
                     "parsed": report.parsed, "checks_fired": report.fired,
                     "call_failures": failures, "variant": args.variant,
                     "elapsed_s": round(elapsed, 2),
                     "trace_id": trace.trace_id})
        print(f"{doc:<9}{str(report.parsed['total']):>12}"
              f"{truth['total_amount']:>11}{outcome:>12}{elapsed:>7.1f}  "
              f"{note[:40]}")

    counts = tally(rows)
    print(f"\n  correct {counts['correct']}, WRONG {counts['WRONG']}, "
          f"caught {counts['caught']}, refused {counts['refused']}, "
          f"false alarms {counts['false_alarm']}  (of {len(rows)})")
    print("  WRONG is the count of extractions that were incorrect and that")
    print("  every check accepted. Those are the ones a human would have had")
    print("  to open the image to find, and nobody opens ten thousand images.")

    write_json("artifacts/week09_extractions.json",
               {"variant": args.variant, "rows": rows, "tally": counts})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
