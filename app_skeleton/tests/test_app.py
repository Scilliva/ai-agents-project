"""The skeleton has to run end to end on day one, with nothing built.

    cd app_skeleton && python -m pytest tests -q

These tests do not call a model and do not touch the network, exactly like
the spine's. They check four things that would quietly break the promise
the skeleton makes: every module imports, every stub says it is a stub, an
all-stub request writes one valid trace, and a batch run writes the traces
week 10 reads, with the keys week 10 gates on.
"""

from __future__ import annotations

import importlib
import json
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
# The spine, when it sits beside the skeleton: in the course folder, and in
# a student repository that kept the unpacked project_spine/.
if (HERE.parent / "project_spine").is_dir():
    sys.path.insert(1, str(HERE.parent / "project_spine"))

from project.contracts import GoldCase, GoldSet  # noqa: E402
from project.trace import read_traces  # noqa: E402
from project.verify import main as verify_main  # noqa: E402

MODULES = ["agent", "agents", "checks", "extractor", "graph", "mcp_server",
           "memory", "pipeline", "retry", "router", "routes", "run", "stub",
           "tools", "vision"]


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    """A throwaway student repository."""
    (tmp_path / "DECISIONS.md").write_text("# Decisions\n", encoding="utf-8")
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
    return tmp_path


# --------------------------------------------------------------------------
# Every module imports, and every stub is marked
# --------------------------------------------------------------------------

@pytest.mark.parametrize("name", MODULES)
def test_the_module_imports_without_a_model(name):
    importlib.import_module(f"app.{name}")


def test_every_stage_starts_as_a_stub():
    from app.pipeline import status
    stages = status()
    assert stages, "no stages registered"
    built = [name for name, s in stages.items() if not s["stub"]]
    assert not built, f"the skeleton ships these as built: {built}"


def test_no_stub_reaches_into_a_solution_folder():
    """The packager rule, checked at source as well as in the archive."""
    word = re.compile(r"\bsolution\b")
    for path in (HERE / "app").glob("*.py"):
        for n, line in enumerate(path.read_text().splitlines(), 1):
            code = line.split("#", 1)[0]
            assert not word.search(code), f"{path.name}:{n}: {line.strip()}"


# --------------------------------------------------------------------------
# One request, all stubs
# --------------------------------------------------------------------------

def test_an_all_stub_request_writes_one_valid_trace(repo, capsys):
    from app.run import main
    assert main(["My heating has been broken for three weeks."]) == 0

    traces = read_traces()
    assert len(traces) == 1
    t = traces[0]
    # Honest: a stub refuses rather than pretending to answer.
    assert t.outcome == "refused"
    assert "help desk" in (t.output or "")
    # It says, in the record, that it is a stub.
    assert t.notes["source"] == "app"
    assert "agent" in t.notes["stubbed"]
    assert all(s.detail.get("stub") is True for s in t.steps)
    # No model was called, and the conditions say so rather than lying.
    assert t.conditions.model == "none"
    assert t.week == 1
    assert verify_main(repo) == 0


def test_a_forced_route_reaches_the_extractor_and_says_it_was_forced(repo):
    """How week 2 is exercised before week 3 has built a router."""
    from app.run import main
    assert main(["--route", "request", "The badge reader is broken."]) == 0
    t = read_traces()[0]
    assert t.notes["route_forced"] is True
    assert [s.name for s in t.steps] == ["memory.search", "route.forced",
                                         "extractor.extract"]
    assert t.outcome == "refused"


def test_an_image_request_is_refused_by_the_stub_vision_step(repo):
    from app.pipeline import handle
    t = handle("Post this invoice.", image="INV-001.png")
    assert t.outcome == "refused"
    assert [s.name for s in t.steps] == ["vision.read_group:identity",
                                         "vision.read_group:amounts"]


def test_a_failing_stage_still_writes_its_trace(repo, monkeypatch):
    """Week 8's rule for the whole pipeline: a crash is recorded, not lost."""
    from app import router
    from app.pipeline import handle

    def broken(client, text, model="", temperature=0.0):
        raise RuntimeError("upstream timeout")

    monkeypatch.setattr(router, "classify", broken)
    t = handle("anything")
    assert t.outcome == "error"
    assert "upstream timeout" in t.notes["error"]
    failed = read_traces()[0].steps[-1]
    assert failed.name == "router.classify" and failed.ok is False
    # A replaced function carries no stub marker, so its step is not a stub.
    assert failed.detail["stub"] is False


# --------------------------------------------------------------------------
# The batch run, which is what week 10 reads
# --------------------------------------------------------------------------

def _goldset(repo: Path) -> Path:
    gs = GoldSet(cases=[
        GoldCase(case_id=f"Q{i:02d}", week_added=2, question=q,
                 expected_behavior="answers or refuses honestly")
        for i, q in enumerate(["Where do I register a new address?",
                               "My bin was not collected.",
                               "How much is a parking vignette?"], 1)])
    path = repo / "goldset.json"
    path.write_text(gs.model_dump_json(), encoding="utf-8")
    return path


def test_a_batch_runs_every_case_twice_with_nobody_present(repo, capsys):
    from app.run import main
    assert main(["--batch", "--goldset", str(_goldset(repo)),
                 "--repeat", "2"]) == 0

    traces = read_traces()
    assert len(traces) == 6
    assert {t.case_id for t in traces} == {"Q01", "Q02", "Q03"}
    assert all(t.notes["unattended"] for t in traces)
    assert verify_main(repo) == 0


def test_batch_traces_carry_what_the_week10_harness_reads(repo):
    """The fields week 10's loader and dimensions use, and its key gate.

    Read as plain dicts, because that is how week 10 reads them.
    """
    from app.run import main
    main(["--batch", "--goldset", str(_goldset(repo)), "--repeat", "2"])
    rows = [json.loads(line) for line in
            (repo / "artifacts" / "traces.jsonl").read_text().splitlines()]

    for t in rows:
        assert t["conditions"]["model"] and t["conditions"]["run_date"]
        assert t["outcome"] in {"ok", "refused", "degraded", "blocked",
                                "error"}
        assert all("ok" in s for s in t["steps"])
    # One set of settings keys per (week, source), which is the gate.
    keys = {(t["week"], t["notes"]["source"],
             frozenset(t["conditions"]["settings"])) for t in rows}
    assert len({(w, s) for w, s, _ in keys}) == len(keys)
    # Same case, same conditions, twice: consistency has evidence.
    by_case: dict[tuple, int] = {}
    for t in rows:
        k = (t["week"], t["case_id"],
             json.dumps(t["conditions"]["settings"], sort_keys=True))
        by_case[k] = by_case.get(k, 0) + 1
    assert set(by_case.values()) == {2}


def test_the_trace_names_the_model_a_built_stage_actually_uses(repo,
                                                                monkeypatch):
    """Read from the stage's own `model` default, never assumed."""
    from app import router
    from app.pipeline import handle

    def classify(client, text, model="qwen2.5:7b", temperature=0.0):
        return None, {"prompt_tokens": 1, "completion_tokens": 1}

    monkeypatch.setattr(router, "classify", classify)
    t = handle("anything")
    assert t.conditions.model == "qwen2.5:7b"
