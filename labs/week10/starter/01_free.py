"""Block 1: everything you can measure for zero model calls.

Your project has been writing traces since week 2. This reads them back and
computes five numbers per week, none of which costs a token. Run it before
you write a single judge, because most of what people reach for a judge to
measure is already sitting in their own logs.

    python 01_free.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "project_spine"))

from dimensions import report  # noqa: E402
from loader import condition_of, load_traces  # noqa: E402

from project.trace import write_json  # noqa: E402

WEEKS = [5, 8, 9]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, default=None)
    args = ap.parse_args()

    if args.week:
        traces = load_traces(args.week)
        print(f"WEEK {args.week}, {len(traces)} traces\n")
        for d in report(traces):
            print("  " + d.line())
        return 0

    everything = load_traces()
    names = ["accuracy", "consistency", "robustness", "predictability",
             "safety"]
    print(f"THE FREE LAYER, {len(everything)} recorded runs, zero model calls\n")
    print(f"{'week':<7}{'runs':>6}" + "".join(f"{n[:9]:>12}" for n in names))
    print("-" * 74)
    rows = {}
    for week in WEEKS:
        traces = load_traces(week, source="lab")
        dims = report(traces)
        rows[week] = {d.name: d.value for d in dims}
        cells = "".join(
            f"{'n/a':>12}" if d.value is None else f"{d.value:>12.2f}"
            for d in dims)
        print(f"{week:<7}{len(traces):>6}{cells}")
    # Your application's own runs, from `python -m app.run`, as one row.
    # They are the system you submit, so this is the row the rest of the
    # semester is about. It is empty until you have run the batch.
    app_traces = load_traces(source="app")
    if app_traces:
        dims = report(app_traces)
        rows["app"] = {d.name: d.value for d in dims}
        print(f"{'app':<7}{len(app_traces):>6}" + "".join(
            f"{'n/a':>12}" if d.value is None else f"{d.value:>12.2f}"
            for d in dims))
    dims_all = report(everything)
    rows["all"] = {d.name: d.value for d in dims_all}
    print(f"{'all':<7}{len(everything):>6}" + "".join(
        f"{'n/a':>12}" if d.value is None else f"{d.value:>12.2f}"
        for d in dims_all))

    print("\n  Read the week 9 row and the week 8 row against each other.")
    print("  Week 9 has the best accuracy in the table and no evidence at")
    print("  all on three of the four reliability dimensions, because it")
    print("  never failed, so there was nothing to be reliable about.")
    print("  Week 8 has the worst accuracy and the best predictability,")
    print("  because its failures were injected on purpose and its code")
    print("  says so when they happen.")
    print("\n  Ranking these three by accuracy puts them in the reverse of")
    print("  the order you would trust them in. That is the AAR-Rabanser")
    print("  finding, reproduced on your own project's logs.")

    print("\n  Two n/a cells are defects rather than absences:")
    for week in WEEKS:
        traces = load_traces(week, source="lab")
        conds = {(t["case_id"], condition_of(t)) for t in traces}
        cases = {c for c, _ in conds}
        if rows[week].get("robustness") is None and cases:
            example = sorted(cases)[0]
            print(f"   week {week}: no case ran under two conditions. Look at")
            print(f"   the case ids, for example {example!r}, and say what")
            print(f"   went wrong when they were named.")

    write_json("artifacts/week10_free.json", {"by_week": rows})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
