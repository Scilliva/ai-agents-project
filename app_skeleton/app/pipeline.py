"""The pipeline: one request in, one answer and one trace out.

This file is not a stub. It is the composition, and the composition is the
part of the project the rubric's second criterion marks. It starts as one
defensible shape for the Remerbaach help desk:

    request ──> memory.search (week 6, retrieval from week 7)
            ──> router (week 3)
                  request route  ──> extractor (week 2) ──> approval gate (week 8)
                  answer route   ──> plan (week 5) ──> agent loop and tools
                                     (week 4) ──> reviewer (week 5)
                  other routes   ──> the route's specialist prompt (week 3)
    image   ──> vision (week 9) ──> checks and triage (week 9) ──> gate (week 8)

with every call that can fail wrapped in the week 8 retry policy. Change it
when your measurements say so, and record the measurement in DECISIONS.md.
A router you removed because it did not beat the monolith is a design
decision. A router you never wired in is a stub, and the trace says which.

Every run writes exactly one `contracts.Trace` to `artifacts/traces.jsonl`
through `project.trace`, which is what week 10's harness reads. Three
choices in that record are deliberate:

  * `notes["source"]` is "app", so week 10 can tell a run of your system
    from a run of a lab script recorded in the same week.
  * `conditions.settings` always carries the same two keys, `skeleton` and
    `stubbed`. Week 10 gates on the keys being consistent, and the list of
    stubs is a condition: a run with the router stubbed and a run with it
    built are runs of two different systems.
  * `week` is the latest increment that is no longer a stub, unless you
    pass one. It changes exactly when the system changes.
"""

from __future__ import annotations

import hashlib
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from project.contracts import Outcome, Trace
from project.models import LARGE, SMALL
from project.trace import TraceRecorder, local_conditions, repo_root

from . import agent, agents, checks, extractor, graph, memory, retry, router
from . import routes, vision
from .stub import stub_info

SKELETON_VERSION = "2026-10"
ANONYMOUS = "anonymous"
HELP_DESK = "Please telephone the help desk on 4796-2222."

# Which routes the agent answers. Everything else, except `request`, goes to
# its week 3 specialist prompt. Yours to change.
AGENT_ROUTES = ("info",)

# One policy per step, chosen in advance by consequence. The stub retry
# module ignores them; week 8's honors them.
SEARCH_POLICY = retry.StepPolicy(attempts=3, max_elapsed=3.0,
                                 on_exhausted="degrade")
AGENT_POLICY = retry.StepPolicy(attempts=2, max_elapsed=60.0,
                                on_exhausted="degrade")


@dataclass
class Request:
    """What the agent loop needs from a task: week 4's `id`, `lang`, and
    `question`."""

    id: str
    question: str
    lang: str = "und"


# --------------------------------------------------------------------------
# Which stages are still stubs
# --------------------------------------------------------------------------

def _mcp_functions() -> list[Any]:
    """The MCP module, imported only to ask whether it is still the stub.

    Your week 6 server needs the `mcp` package at import time, and the
    pipeline itself never needs it, so a server that cannot be imported
    here counts as built rather than breaking every run.
    """
    try:
        from . import mcp_server
    except (ImportError, SystemExit):
        return []
    return [mcp_server.recall]


STAGES: list[tuple[str, int, Any]] = [
    ("extract", 2, lambda: [extractor.extract]),
    ("route", 3, lambda: [router.classify, router.apply_policy]),
    ("agent", 4, lambda: [agent.run_task]),
    ("plan", 5, lambda: [agents.make_plan, agents.validate_plan,
                         agents.review]),
    # Week 7 has no row of its own: retrieval replaces the body of this
    # same `search`, so the memory stage stands for weeks 6 and 7.
    ("memory", 6, lambda: [memory.MemoryStore.search]),
    ("mcp", 6, _mcp_functions),
    ("retry", 8, lambda: [retry.call_with_policy]),
    ("gate", 8, lambda: [graph.request_approval]),
    ("vision", 9, lambda: [vision.read_group]),
    ("checks", 9, lambda: [checks.run_checks, checks.code_triage]),
]


def status() -> dict[str, dict[str, Any]]:
    """Each stage, its week, and whether any of its functions is a stub."""
    out = {}
    for name, week, functions in STAGES:
        infos = [stub_info(fn) for fn in functions()]
        stubbed = [i for i in infos if i is not None]
        out[name] = {"week": week, "stub": bool(stubbed),
                     "does": stubbed[0]["does"] if stubbed else "built"}
    return out


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

class _LazyClient:
    """The model client, created on first use.

    A pipeline whose stages are all stubs never calls a model, so it must
    not need the `openai` package or a running server. This defers both
    until a built stage actually makes a call.
    """

    def __init__(self) -> None:
        self._real = None

    def __getattr__(self, name: str) -> Any:
        if self._real is None:
            from project.models import client_for
            self._real = client_for()
        return getattr(self._real, name)


def _mark(span, fn: Any, week: int) -> bool:
    """Record on the step whether it ran a stub. Returns True for a stub."""
    info = stub_info(fn)
    span.detail(stub=info is not None, week=week)
    if info is not None:
        span.detail(does=info["does"])
    return info is not None


def _model_of(fn: Any, fallback: str) -> str:
    """The model a built stage calls, read from its `model` default.

    The trace must name the model that actually ran, and the week files
    choose it through that default. Change the default and the trace
    follows, instead of recording a model the stage no longer uses.
    """
    try:
        default = inspect.signature(fn).parameters["model"].default
    except (KeyError, TypeError, ValueError):
        return fallback
    if isinstance(default, str) and default:
        return default
    return getattr(default, "name", None) or fallback


def case_id_for(text: str) -> str:
    """A stable id for an ad hoc request, so reruns of it can be compared."""
    return "adhoc-" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


class _Run:
    """What one request accumulates on its way through."""

    def __init__(self, rec: TraceRecorder, case_id: str, unattended: bool):
        self.rec = rec
        self.case_id = case_id
        self.unattended = unattended
        self.client = _LazyClient()
        self.models: set[str] = set()
        self.missing: list[str] = []
        self.notes: dict[str, Any] = {}


# --------------------------------------------------------------------------
# The stages, in the order a request meets them
# --------------------------------------------------------------------------

def _recall(run: _Run, subject: str, text: str) -> list[str]:
    with run.rec.step("retrieval", "memory.search") as s:
        _mark(s, memory.MemoryStore.search, 6)
        store = memory.MemoryStore.load(repo_root() / memory.DEFAULT_PATH)
        res = retry.call_with_policy(store.search, subject, text, k=3,
                                     policy=SEARCH_POLICY)
        facts = [str(f) for f in (res.value or [])] if res.ok else []
        s.detail(hits=len(facts), tries=res.tries, outcome=res.outcome)
        if not res.ok:
            run.missing.append("memory")
    return facts


def _gate(run: _Run, payload: dict) -> dict:
    with run.rec.step("approval", "graph.request_approval") as s:
        _mark(s, graph.request_approval, 8)
        decision = graph.request_approval(payload,
                                          unattended=run.unattended)
        s.detail(action=payload["action"],
                 verdict=decision.get("verdict"), by=decision.get("by"))
    return decision


def _submit(run: _Run, text: str, facts: list[str]) -> tuple[str, Outcome]:
    """The request route: extract a record, then ask before submitting."""
    with run.rec.step("model", "extractor.extract") as s:
        if not _mark(s, extractor.extract, 2):
            run.models.add(_model_of(extractor.extract, SMALL.name))
        record, meta = extractor.extract(run.client, extractor.SYSTEM, text)
        s.tokens(meta.get("prompt_tokens"), meta.get("completion_tokens"))
        s.detail(valid=record is not None, error=meta.get("error"))
    if record is None:
        return ("I could not turn this message into a request, so nothing "
                f"was logged. {HELP_DESK}"), "refused"

    arguments = record.model_dump()
    decision = _gate(run, {
        "action": "submit_case", "case_id": run.case_id,
        "arguments": arguments, "evidence": [record.quote, *facts],
        "degraded": bool(run.missing), "missing": sorted(run.missing)})
    verdict = decision.get("verdict")
    if verdict in ("approve", "edit"):
        if verdict == "edit":
            arguments = decision.get("arguments") or arguments
        return (f"Logged a {arguments.get('category')} request, urgency "
                f"{arguments.get('urgency')}."), "ok"
    return (f"Not submitted: the approval gate answered {verdict} "
            f"({decision.get('by')})."), "blocked"


def _answer(run: _Run, text: str, facts: list[str]) -> tuple[str, Outcome]:
    """The answer route: plan, run the agent loop, then review."""
    with run.rec.step("model", "agents.make_plan") as s:
        if not _mark(s, agents.make_plan, 5):
            run.models.add(getattr(agents, "MODEL_NAME", LARGE.name))
        plan = agents.make_plan(text)
        plan_ok, problems = agents.validate_plan(plan)
        s.detail(steps=len(plan.steps), plan_ok=plan_ok, problems=problems)
    if not plan_ok:
        run.notes["plan_problems"] = problems
        return f"I could not plan an answer to this. {HELP_DESK}", "refused"

    question = text
    if facts:
        question += "\n\nWhat is already known:\n" + "\n".join(
            f"- {f}" for f in facts)
    task = Request(id=run.case_id, question=question)

    with run.rec.step("model", "agent.run_task") as s:
        agent_stub = _mark(s, agent.run_task, 4)
        if not agent_stub:
            run.models.add(_model_of(agent.run_task, LARGE.name))
        res = retry.call_with_policy(agent.run_task, run.client, task,
                                     policy=AGENT_POLICY)
        result = res.value
        s.detail(tries=res.tries, outcome=res.outcome)
        failed = [a.error for a in res.attempts if a.error]
        if failed:
            run.notes["call_failures"] = len(failed)
        if result is not None:
            s.tokens(result.tokens or None, None)
            s.detail(steps=result.steps, tool_calls=result.tool_calls,
                     cap_fired=result.cap_fired,
                     tool_errors=result.tool_errors,
                     saw_injection=result.saw_injection)
    if result is None or not res.ok:
        run.missing.append("agent")
        return f"I could not answer this right now. {HELP_DESK}", "degraded"
    if agent_stub:
        return result.answer, "refused"

    with run.rec.step("check", "agents.review") as s:
        _mark(s, agents.review, 5)
        verdict = agents.review(text, result.answer, facts)
        s.detail(verdict=verdict.decision if verdict else None,
                 reason=verdict.reason if verdict else None)
    if verdict is not None and verdict.decision == "reject":
        return (f"I have a draft answer but it did not pass review. "
                f"{HELP_DESK}"), "blocked"
    if result.cap_fired:
        return result.answer, "degraded"
    return result.answer, "ok"


def _specialist(run: _Run, route: str, text: str) -> tuple[str, Outcome]:
    with run.rec.step("model", f"router.respond:{route}") as s:
        stubbed = _mark(s, router.respond, 3)
        if not stubbed:
            run.models.add(_model_of(router.respond, SMALL.name))
        answer, meta = router.respond(run.client,
                                      routes.SPECIALISTS.get(route, ""), text)
        s.tokens(meta.get("prompt_tokens"), meta.get("completion_tokens"))
    return answer, "refused" if stubbed else "ok"


def _text(run: _Run, text: str, subject: str,
          route: str | None) -> tuple[str, Outcome]:
    facts = _recall(run, subject, text)

    if route:
        # Forced from the command line, so that one path can be exercised
        # on its own, for example the week 2 extractor before the week 3
        # router exists. Recorded, because a forced route is not a routed
        # one and week 10 should not score it as if it were.
        with run.rec.step("check", "route.forced") as s:
            s.detail(stub=False, week=3, route=route)
        run.notes["route"] = route
        run.notes["route_forced"] = True
        return _dispatch(run, route, text, facts)

    with run.rec.step("model", "router.classify") as s:
        if not _mark(s, router.classify, 3):
            run.models.add(_model_of(router.classify, SMALL.name))
        decision, meta = router.classify(run.client, text)
        s.tokens(meta.get("prompt_tokens"), meta.get("completion_tokens"))
    with run.rec.step("check", "router.apply_policy") as s:
        _mark(s, router.apply_policy, 3)
        routed = router.apply_policy(decision, text)
        s.detail(route=routed.applied_route, policy_fired=routed.policy_fired)
    run.notes["route"] = routed.applied_route
    return _dispatch(run, routed.applied_route, text, facts)


def _dispatch(run: _Run, route: str, text: str,
              facts: list[str]) -> tuple[str, Outcome]:
    if route == "request":
        return _submit(run, text, facts)
    if route in AGENT_ROUTES:
        return _answer(run, text, facts)
    return _specialist(run, route, text)


def _image(run: _Run, text: str, image: Path) -> tuple[str, Outcome]:
    """A request with an image: read it, check it, and triage it."""
    fields: dict[str, Any] = {}
    failures = 0
    for group, names in checks.GROUPS.items():
        with run.rec.step("model", f"vision.read_group:{group}") as s:
            if not _mark(s, vision.read_group, 9):
                run.models.add(vision.MODEL)
            result = vision.read_group(image, group, names)
            s.tokens(result.prompt_tokens or None,
                     result.output_tokens or None)
            s.detail(failure=result.failure)
            if result.failure:
                failures += 1
            else:
                fields.update(result.fields)
    run.notes["call_failures"] = failures
    if not fields:
        return f"I could not read this image. {HELP_DESK}", "refused"

    with run.rec.step("check", "checks.run_checks") as s:
        _mark(s, checks.run_checks, 9)
        report = checks.run_checks(fields)
        s.detail(fired=report.fired)
    run.notes["checks_fired"] = list(report.fired)
    with run.rec.step("check", "checks.code_triage") as s:
        _mark(s, checks.code_triage, 9)
        may_skip, why = checks.code_triage(fields, report)
        s.detail(may_skip=may_skip, reason=why)
    if may_skip:
        return f"Posted automatically: {why}", "ok"

    decision = _gate(run, {
        "action": "post_invoice", "case_id": run.case_id,
        "arguments": fields, "evidence": list(report.fired) or [why],
        "degraded": failures > 0, "missing": sorted(run.missing)})
    if decision.get("verdict") in ("approve", "edit"):
        return "Posted after approval.", "ok"
    return (f"Held for a person: the approval gate answered "
            f"{decision.get('verdict')} ({decision.get('by')})."), "blocked"


# --------------------------------------------------------------------------
# The entry points
# --------------------------------------------------------------------------

def handle(text: str, *, case_id: str | None = None,
           subject: str | None = None, image: str | Path | None = None,
           route: str | None = None, week: int | None = None,
           unattended: bool = False,
           persist: bool = True, path: str | Path | None = None) -> Trace:
    """Push one request through every stage and record one trace.

    A stage that raises does not lose the run: the step records the error,
    the outcome is "error", and the trace is still written. Week 8's point,
    applied to the whole pipeline: a failure you did not record is a
    failure you cannot count.
    """
    stages = status()
    stubbed = [name for name, s in stages.items() if s["stub"]]
    built_weeks = [s["week"] for s in stages.values() if not s["stub"]]
    rec = TraceRecorder(
        week=week or max(built_weeks, default=1),
        case_id=case_id or case_id_for(text),
        conditions=local_conditions("none", temperature=0.0,
                                    skeleton=SKELETON_VERSION,
                                    stubbed=",".join(stubbed) or "none"),
        user_input=text)
    run = _Run(rec, rec.case_id, unattended)

    output: str | None
    try:
        if image:
            output, outcome = _image(run, text, Path(image))
        else:
            output, outcome = _text(run, text, subject or ANONYMOUS, route)
    except Exception as exc:                              # noqa: BLE001
        output, outcome = None, "error"
        run.notes["error"] = f"{type(exc).__name__}: {exc}"[:300]

    rec.conditions.model = "+".join(sorted(run.models)) or "none"
    if run.missing:
        run.notes["missing"] = sorted(set(run.missing))
    return rec.finish(output=output, outcome=outcome, persist=persist,
                      path=path, source="app", stubbed=stubbed,
                      skeleton=SKELETON_VERSION, unattended=unattended,
                      **run.notes)


def run_batch(cases, repeat: int = 1, week: int | None = None,
              path: str | Path | None = None) -> list[Trace]:
    """Every gold case, `repeat` times, with nobody present.

    This is what week 10 needs: the same cases run more than once under the
    same conditions, so that consistency can be measured, and no step that
    waits for a human, so that it can run overnight.
    """
    traces = []
    for _ in range(repeat):
        for case in cases:
            traces.append(handle(case.question, case_id=case.case_id,
                                 week=week, unattended=True, path=path))
    return traces
