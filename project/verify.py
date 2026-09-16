"""Check that your artifacts still match the contract.

    python -m project.verify

Run it at the end of every session, before you commit. It is the difference
between finding out in week 10 that your week 7 gold set has a field the
harness cannot read, and finding out in week 7.

It reports rather than raises, so you see every problem at once instead of
the first one. Exit code is 1 when something is wrong, so you can put it in
a pre-commit hook if you like that sort of thing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic import ValidationError

from .contracts import (FINDINGS_PATH, GOLDSET_PATH, GUARD_LOG_PATH,
                        SCHEMA_VERSION, TRACES_PATH, Finding, GoldSet,
                        GuardEvent, Trace)
from .trace import repo_root

OK = "  ok  "
BAD = " FAIL "
SKIP = " skip "


def _report(status: str, name: str, detail: str = "") -> None:
    print(f"[{status}] {name:<28} {detail}")


def _check_jsonl(path: Path, model, name: str) -> list[str]:
    if not path.exists():
        _report(SKIP, name, "not written yet")
        return []
    problems, count, stale = [], 0, 0
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(),
                             start=1):
        if not line.strip():
            continue
        count += 1
        try:
            obj = model.model_validate_json(line)
        except ValidationError as exc:
            first = exc.errors()[0]
            loc = ".".join(str(p) for p in first["loc"])
            problems.append(f"{path.name}:{n} field {loc!r}: {first['msg']}")
            continue
        if getattr(obj, "schema_version", SCHEMA_VERSION) != SCHEMA_VERSION:
            stale += 1
    if problems:
        _report(BAD, name, f"{len(problems)} of {count} records are invalid")
    else:
        note = f"{count} records"
        if stale:
            note += (f", {stale} written against an older schema "
                     f"(current is {SCHEMA_VERSION})")
        _report(OK, name, note)
    return problems


def _check_json(path: Path, model, name: str) -> list[str]:
    if not path.exists():
        _report(SKIP, name, "not written yet")
        return []
    try:
        model.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        first = exc.errors()[0]
        loc = ".".join(str(p) for p in first["loc"])
        _report(BAD, name, f"field {loc!r}: {first['msg']}")
        return [f"{path.name} field {loc!r}: {first['msg']}"]
    except json.JSONDecodeError as exc:
        _report(BAD, name, f"not valid json: {exc}")
        return [f"{path.name}: {exc}"]
    _report(OK, name, "valid")
    return []


def _check_findings(path: Path) -> list[str]:
    """Findings get one extra rule that the schema cannot express."""
    if not path.exists():
        _report(SKIP, "findings.json", "not written yet")
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        findings = [Finding.model_validate(f) for f in raw]
    except (ValidationError, json.JSONDecodeError) as exc:
        _report(BAD, "findings.json", str(exc)[:80])
        return [str(exc)]
    open_claims = [f.finding_id for f in findings
                   if f.mitigation and not f.regression_test
                   and not f.accepted_residual]
    if open_claims:
        _report(BAD, "findings.json",
                f"{len(open_claims)} claim a mitigation with no regression "
                f"test: {', '.join(open_claims)}")
        return [f"finding {i} is not closed" for i in open_claims]
    _report(OK, "findings.json", f"{len(findings)} findings")
    return []


def main(root: Path | None = None) -> int:
    base = root or repo_root()
    print(f"Verifying artifacts under {base}\n")

    problems: list[str] = []
    problems += _check_jsonl(base / TRACES_PATH, Trace, "traces.jsonl")
    problems += _check_json(base / GOLDSET_PATH, GoldSet, "goldset.json")
    problems += _check_jsonl(base / GUARD_LOG_PATH, GuardEvent,
                             "guard_events.jsonl")
    problems += _check_findings(base / FINDINGS_PATH)

    print()
    if problems:
        print(f"{len(problems)} problem(s). The first few:")
        for p in problems[:8]:
            print(f"  - {p}")
        print("\nA contract failure now is a week 10 failure you have been "
              "spared. Fix the writer, not the contract.")
        return 1
    print("All artifacts match the contract.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
