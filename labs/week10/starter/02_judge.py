"""Block 2: a judge, validated against labels you wrote first.

Three steps, in this order, and the order is the argument:

  1. label     twelve cases by hand, before any judge runs
  2. judge     score the same twelve
  3. sweep     vary the threshold and watch agreement move

Step 3 is the one that matters. A judge is not a model, it is a model AND a
threshold, and reporting the first without the second describes half an
instrument.

    python 02_judge.py --replay     # the recorded judgments, instant
    python 02_judge.py              # live, about fifty seconds
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "project_spine"))

import judge as J  # noqa: E402

from project.trace import write_json  # noqa: E402

SWEEP = [0.15, 0.25, 0.35, 0.45, 0.50, 0.55, 0.65, 0.75, 0.85]


def collect(replay: bool) -> dict[str, J.Judgment]:
    recorded = J.load_recorded()
    if replay:
        if not recorded:
            print("no fixture at fixtures/judgments.json. Run without "
                  "--replay once.")
            sys.exit(1)
        return recorded
    metric = J.build_metric()
    for case in J.LABELS:
        if case.case_id in recorded:
            continue
        judgment = J.judge_one(metric, case)
        recorded[case.case_id] = judgment
        J.save_recorded(recorded)      # written as it goes, so a kill costs one call
        print(f"  {case.case_id} {judgment.verdict:<5} "
              f"{judgment.score:.2f} ({judgment.seconds}s)", flush=True)
    return recorded


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    args = ap.parse_args()

    judgments = collect(args.replay)
    agreement = J.validate(judgments)

    print(f"\nJUDGE AGAINST HAND LABELS, threshold {J.THRESHOLD}\n")
    print(f"{'case':<7}{'human':>7}{'judge':>7}{'score':>7}   why the human said so")
    print("-" * 76)
    for row in agreement.rows:
        flag = "" if row["human"] == row["judge"] else "  <-- DISAGREE"
        print(f"{row['case_id']:<7}{row['human']:>7}{row['judge']:>7}"
              f"{row['score']:>7.2f}   {row['why_human'][:32]:<34}{flag}")
    print(f"\n  agreement {agreement.agreed}/{agreement.n} = "
          f"{agreement.rate:.2f}   {agreement.confusion()}")

    print(f"\nTHE SAME JUDGMENTS AT OTHER THRESHOLDS\n")
    print(f"{'threshold':>10}{'agreement':>11}{'false_pass':>12}"
          f"{'false_fail':>12}")
    print("-" * 47)
    labels = {c.case_id: c.human for c in J.LABELS}
    sweep_rows = []
    for threshold in SWEEP:
        agreed = false_pass = false_fail = 0
        for case_id, judgment in judgments.items():
            verdict = "pass" if judgment.score >= threshold else "fail"
            if labels[case_id] == verdict:
                agreed += 1
            elif verdict == "pass":
                false_pass += 1
            else:
                false_fail += 1
        rate = agreed / len(judgments)
        sweep_rows.append({"threshold": threshold, "agreement": rate,
                           "false_pass": false_pass, "false_fail": false_fail})
        print(f"{threshold:>10.2f}{rate:>11.2f}{false_pass:>12}"
              f"{false_fail:>12}")

    perfect = [r["threshold"] for r in sweep_rows if r["agreement"] == 1.0]
    if perfect:
        print(f"\n  Perfect agreement holds only on {min(perfect)} to "
              f"{max(perfect)}.")
    print("  Nobody chose 0.5. It is the library default, and on this data it")
    print("  happens to land in the middle of the only band that works.")
    print("\n  The two mistakes are not symmetric, and that is the sentence")
    print("  to put in your report. Too low and you get false PASSES: the")
    print("  gate is green and the answer was invented. Too high and you get")
    print("  false fails, which cost a human's attention and nothing worse.")
    print("  So if you must be wrong, be wrong on the high side.")

    total = sum(r["seconds"] for r in agreement.rows)
    print(f"\n  cost: {total:.0f}s for {agreement.n} cases, about "
          f"{total / max(agreement.n, 1):.1f}s each, against microseconds")
    print("  for a deterministic check. Judge only what a check cannot reach.")

    write_json("artifacts/week10_judge.json",
               {"threshold": J.THRESHOLD, "rows": agreement.rows,
                "confusion": agreement.confusion(), "sweep": sweep_rows})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
