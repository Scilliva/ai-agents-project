"""Recording a run, and reading it back.

Build the diagnostic before the measurement. When something fails, the
first question is always what the system actually did, and if that was not
captured you are guessing. So the trace is written first, from week 1, and
every later week reads it.

Typical use inside a lab:

    from project.trace import TraceRecorder, local_conditions

    rec = TraceRecorder(week=4, case_id="T-01",
                        conditions=local_conditions("qwen3:4b-instruct"),
                        user_input=task.question)

    with rec.step("model", "qwen3:4b-instruct") as s:
        reply = call_the_model(...)
        s.tokens(reply.input_tokens, reply.output_tokens)

    with rec.step("tool", "search_services") as s:
        s.detail(query=q)
        hits = search(q)
        s.detail(hits=len(hits))

    rec.finish(output=answer, outcome="ok")   # writes to artifacts/

Reading them back, which is what weeks 10 to 13 do:

    from project.trace import read_traces
    for t in read_traces():
        print(t.case_id, t.outcome, t.total_tokens, t.step_count)
"""

from __future__ import annotations

import json
import os
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .contracts import (SCHEMA_VERSION, TRACES_PATH, Conditions, Outcome,
                        Step, StepKind, Trace)


def repo_root() -> Path:
    """The repository root, so that artifact paths do not depend on cwd.

    Walks up from this file looking for the marker that week 1 creates. If
    you moved things around, set PROJECT_ROOT and it will be believed.
    """
    override = os.environ.get("PROJECT_ROOT")
    if override:
        return Path(override).resolve()
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "DECISIONS.md").exists() or (parent / ".git").exists():
            return parent
    return here.parent.parent


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def local_conditions(model: str, temperature: float = 0.0,
                     **settings: Any) -> Conditions:
    """Conditions for a locally served model, with today's date filled in.

    Everything you pass as a keyword lands in `settings`. Use it for the
    week specific things: chunk_size, k, resolution, prompt_version.
    """
    return Conditions(model=model, temperature=temperature, endpoint="local",
                      run_date=utc_now(), settings=dict(settings))


class _StepHandle:
    """Handed to you inside `with rec.step(...)`. Times itself."""

    def __init__(self, kind: StepKind, name: str, index: int):
        self._kind, self._name, self._index = kind, name, index
        self._detail: dict[str, Any] = {}
        self._in: int | None = None
        self._out: int | None = None
        self.ok = True
        self._t0 = time.perf_counter()

    def tokens(self, input_tokens: int | None,
               output_tokens: int | None) -> None:
        self._in, self._out = input_tokens, output_tokens

    def detail(self, **kw: Any) -> None:
        """Add to the step detail. Call it as often as you like.

        Do not put raw user input here if a guardrail exists to catch
        personal data in it. Week 11 makes that mistake for you once.
        """
        self._detail.update(kw)

    def failed(self, reason: str) -> None:
        self.ok = False
        self._detail["error"] = reason

    def _build(self) -> Step:
        return Step(index=self._index, kind=self._kind, name=self._name,
                    ok=self.ok,
                    latency_ms=(time.perf_counter() - self._t0) * 1000,
                    input_tokens=self._in, output_tokens=self._out,
                    detail=self._detail)


class TraceRecorder:
    """Collects steps, then produces a Trace you can append to disk."""

    def __init__(self, week: int, case_id: str, conditions: Conditions,
                 user_input: str, trace_id: str | None = None):
        self.week = week
        self.case_id = case_id
        self.conditions = conditions
        self.user_input = user_input
        self.trace_id = trace_id or uuid.uuid4().hex[:12]
        self.started_at = utc_now()
        self._steps: list[Step] = []
        self._trace: Trace | None = None

    @contextmanager
    def step(self, kind: StepKind, name: str) -> Iterator[_StepHandle]:
        handle = _StepHandle(kind, name, len(self._steps))
        try:
            yield handle
        except Exception as exc:                          # noqa: BLE001
            handle.failed(f"{type(exc).__name__}: {exc}")
            self._steps.append(handle._build())
            raise
        self._steps.append(handle._build())

    def finish(self, output: str | None, outcome: Outcome,
               persist: bool = True, path: str | Path | None = None,
               **notes: Any) -> Trace:
        """Close the run, write it to disk, and hand it back.

        Writing is the default rather than a second call you have to
        remember. A run you forgot to persist is a run that did not happen,
        and week 10 cannot evaluate what week 4 threw away. Pass
        `persist=False` when you are experimenting and do not want the file
        to grow.
        """
        self._trace = Trace(
            schema_version=SCHEMA_VERSION, trace_id=self.trace_id,
            week=self.week, case_id=self.case_id, started_at=self.started_at,
            conditions=self.conditions, input=self.user_input,
            steps=self._steps, output=output, outcome=outcome,
            notes=dict(notes))
        if persist:
            append_trace(self._trace, path)
        return self._trace


def append_trace(trace: Trace, path: str | Path | None = None) -> Path:
    target = Path(path) if path else repo_root() / TRACES_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fh:
        fh.write(trace.model_dump_json() + "\n")
    return target


def read_traces(path: str | Path | None = None,
                week: int | None = None) -> list[Trace]:
    """Load every trace, optionally filtered to one week.

    A malformed line is a defect worth seeing, not worth skipping, so this
    raises rather than swallowing it. `python -m project.verify` gives you a
    friendlier report.
    """
    target = Path(path) if path else repo_root() / TRACES_PATH
    if not target.exists():
        return []
    out: list[Trace] = []
    for n, line in enumerate(target.read_text(encoding="utf-8").splitlines(),
                             start=1):
        if not line.strip():
            continue
        try:
            trace = Trace.model_validate_json(line)
        except Exception as exc:                          # noqa: BLE001
            raise ValueError(
                f"{target}:{n} does not match the Trace contract. Run "
                f"`python -m project.verify` for the details.\n  {exc}"
            ) from exc
        if week is None or trace.week == week:
            out.append(trace)
    return out


def write_json(path: str | Path, payload: Any) -> Path:
    """Small helper, so that every week writes json the same way."""
    target = repo_root() / path if not Path(path).is_absolute() else Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = (payload.model_dump() if hasattr(payload, "model_dump")
            else payload)
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    return target
