"""Block 2: break it on purpose, and find out what your checks can see.

Two experiments, and they answer different questions.

  --sweep   six degradations x five documents. Where is the operating limit,
            and does the model invent a number or refuse to give one?
  --naive   the same five documents read with ONE call for all six fields,
            the obvious implementation, compared against the grouped calls.

Start the live sweep at the beginning of the block and read it at the end.
It is about six minutes. Everything here replays instantly with --replay.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "project_spine"))

from checks import ALL_FIELDS, GROUPS, classify, run_checks, tally  # noqa: E402
from perturb import SWEEP, describe  # noqa: E402
from vision import Fixture, find_fixture, read_group  # noqa: E402

from project.trace import write_json  # noqa: E402

IMAGES = Path(__file__).resolve().parent.parent / "images"
DOCS = ["INV-001", "INV-002", "INV-003", "INV-004", "INV-005"]
SHORT = {"correct": "ok", "WRONG": "WRONG", "caught": "caught",
         "refused": "refuse", "false_alarm": "alarm"}


def truth_for(doc: str) -> dict:
    data = json.loads((IMAGES / "ground_truth.json").read_text())
    return next(r for r in data["documents"] if r["document_id"] == doc)


def read_doc(doc: str, variant: str, groups: dict, replay) -> tuple[dict, list]:
    fields: dict[str, str | None] = {}
    results = []
    for group, group_fields in groups.items():
        res = read_group(IMAGES / f"{doc}.png", group, group_fields,
                         variant=variant, replay=replay)
        results.append(res)
        fields.update(res.fields if res.ok
                      else {f: None for f in group_fields})
    return fields, results


def sweep(replay) -> dict:
    print("DEGRADATION SWEEP, scored on all three amounts\n")
    print(f"{'variant':<20}" + "".join(f"{d[-3:]:>9}" for d in DOCS)
          + "     WRONG")
    print("-" * 82)
    table = {}
    for variant in SWEEP:
        rows, cells = [], []
        for doc in DOCS:
            fields, _ = read_doc(doc, variant, GROUPS, replay)
            report = run_checks(fields)
            outcome = classify(truth_for(doc), report)
            rows.append({"doc": doc, "outcome": outcome,
                         "parsed": report.parsed,
                         "checks_fired": report.fired})
            cells.append(outcome)
        counts = tally(rows)
        table[variant] = {"rows": rows, "tally": counts}
        print(f"{variant:<20}" + "".join(f"{SHORT[c]:>9}" for c in cells)
              + f"{counts['WRONG']:>10}")

    print("\n  Read the WRONG column first. It is the count of extractions")
    print("  that were incorrect AND passed every check, which is the only")
    print("  kind a human would have had to open the image to catch.")
    print("\n  Then ask two questions of the table:")
    print("   1. Which variants changed nothing? Say why that is a result.")
    print("   2. Which DOCUMENT fails first, and what is different about it?")
    return table


def naive(replay) -> dict:
    """One call for all six fields, against two calls of three."""
    print("\nARCHITECTURE COMPARISON on the clean images\n")
    print(f"{'doc':<9}{'grouped':>10}{'g s':>7}{'naive':>10}{'n s':>7}"
          f"   guard on the naive call")
    print("-" * 78)
    rows = []
    for doc in DOCS:
        truth = truth_for(doc)
        g_fields, g_res = read_doc(doc, "clean", GROUPS, replay)
        g_out = classify(truth, run_checks(g_fields))
        n_res = read_group(IMAGES / f"{doc}.png", "naive", ALL_FIELDS,
                           variant="clean", replay=replay)
        n_fields = n_res.fields if n_res.ok else {f: None for f in ALL_FIELDS}
        n_out = classify(truth, run_checks(n_fields))
        g_time = sum(r.elapsed_s for r in g_res)
        rows.append({"doc": doc, "grouped": g_out, "naive": n_out,
                     "grouped_s": round(g_time, 1),
                     "naive_s": round(n_res.elapsed_s, 1),
                     "naive_failure": n_res.failure,
                     "grouped_out_tokens": max(r.output_tokens
                                               for r in g_res),
                     "naive_out_tokens": n_res.output_tokens})
        print(f"{doc:<9}{SHORT[g_out]:>10}{g_time:>7.1f}{SHORT[n_out]:>10}"
              f"{n_res.elapsed_s:>7.1f}   {n_res.failure or '-'}")

    g_tok = max(r["grouped_out_tokens"] for r in rows)
    n_tok = max(r["naive_out_tokens"] for r in rows)
    g_total = sum(r["grouped_s"] for r in rows)
    n_total = sum(r["naive_s"] for r in rows)
    print(f"\n  total wall clock: grouped {g_total:.0f}s, naive {n_total:.0f}s")
    print(f"  largest output:   grouped {g_tok} tokens, naive {n_tok} tokens")
    print("\n  If both columns say ok, that is the finding, not a "
          "disappointment.")
    print("  The naive version is not broken. It is UNRELIABLE, which is")
    print("  worse, because it passes the test you were going to run.")
    print("  WEEK09_FINDINGS.md records three ways it has been seen to fail")
    print("  silently. None of them reproduced here. Design for the failure")
    print("  you cannot reproduce: that is what guard() is for.")
    return {"rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--naive", action="store_true")
    args = ap.parse_args()
    if not (args.sweep or args.naive):
        args.sweep = args.naive = True

    replay = Fixture(find_fixture()) if args.replay else None
    if replay is not None and not replay.entries:
        print("no fixture found at fixtures/vision_runs.jsonl")
        return 1

    out: dict = {"variants": {v: describe(v) for v in SWEEP}}
    if args.sweep:
        out["sweep"] = sweep(replay)
    if args.naive:
        out["architecture"] = naive(replay)
    write_json("artifacts/week09_break.json", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
