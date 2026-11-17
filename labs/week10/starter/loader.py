"""Reload what weeks 2 to 9 wrote. Given: this is plumbing, not the exercise.

Week 10 is the first session that consumes rather than produces. Everything
it reads was written by your own earlier sessions through the same `Trace`
contract, which is the reason this file is forty lines instead of a parser.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "project_spine"))

from project.contracts import GOLDSET_PATH, TRACES_PATH  # noqa: E402

ARTIFACTS = REPO / "artifacts"

# The course's own 62 traces (weeks 5, 8, and 9), shipped with the starter
# for a repository that has none yet. Used only when your own file is
# missing or empty, and announced when it is: an evaluation of the
# reference is a measurement of the reference, not of your system.
REFERENCE_TRACES = (Path(__file__).resolve().parents[1] / "fixtures"
                    / "reference_traces.jsonl")
_announced = False


def traces_path() -> tuple[Path, bool]:
    """Where the traces come from, and whether that is the reference."""
    own = Path(TRACES_PATH)
    if not own.is_absolute():
        own = REPO / own
    if own.exists() and own.read_text().strip():
        return own, False
    return REFERENCE_TRACES, True


def source_of(trace: dict) -> str:
    """Who wrote the run: "app" for your application, "lab" otherwise.

    Your application marks its traces with notes["source"] = "app". Lab
    scripts recorded in the same week do not, and the two are different
    systems, so they are reported apart and gated apart.
    """
    return (trace.get("notes") or {}).get("source", "lab")


def load_traces(week: int | None = None,
                source: str | None = None) -> list[dict]:
    """Every recorded run, optionally for one week or one source."""
    global _announced
    path, reference = traces_path()
    if reference and not _announced:
        _announced = True
        print("NOTE: your artifacts/traces.jsonl is missing or empty, so this "
              "reads the course's\n      reference traces "
              "(fixtures/reference_traces.jsonl). Run your own system\n"
              "      and these numbers become yours.\n", file=sys.stderr)
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text().splitlines()
            if line.strip()]
    return [r for r in rows if (week is None or r["week"] == week)
            and (source is None or source_of(r) == source)]


def load_goldset() -> list[dict]:
    path = Path(GOLDSET_PATH)
    if not path.is_absolute():
        path = REPO / path
    return json.loads(path.read_text())["cases"]


def load_artifact(name: str) -> dict:
    return json.loads((ARTIFACTS / name).read_text())


def by_case(traces: list[dict]) -> dict[tuple[int, str], list[dict]]:
    """Group runs of the SAME case, which is what consistency needs."""
    out: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for t in traces:
        out[(t["week"], t["case_id"])].append(t)
    return dict(out)


def condition_of(trace: dict) -> str:
    """A stable, printable name for the run conditions.

    Sorted, so two traces with the same settings written in a different
    order produce the same string. That sounds pedantic until you group by
    it and get two groups where there is one.
    """
    settings = trace.get("conditions", {}).get("settings") or {}
    interesting = {k: v for k, v in settings.items() if k != "replay"}
    if not interesting:
        return "default"
    return ",".join(f"{k}={interesting[k]}" for k in sorted(interesting))
