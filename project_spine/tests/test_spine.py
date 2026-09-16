"""The spine has to hold, because thirteen weeks are bolted to it.

    cd project_spine && python -m pytest tests -q

These tests do not call a model and do not touch the network. They check
the three things that would quietly break a handover: the trace survives a
round trip to disk, the replay fixture answers the call your code actually
makes, and the verifier notices when an artifact stops matching the
contract.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project.contracts import (SCHEMA_VERSION, GoldCase, GoldSet,  # noqa: E402
                               Trace)
from project.fixtures import (FixtureMiss, ReplayClient,  # noqa: E402
                              call_key, load_or_reference)
from project.prices import estimate  # noqa: E402
from project.trace import (TraceRecorder, local_conditions,  # noqa: E402
                           read_traces, write_json)
from project.verify import main as verify_main  # noqa: E402


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    """A throwaway student repository."""
    (tmp_path / "DECISIONS.md").write_text("# Decisions\n", encoding="utf-8")
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
    return tmp_path


# --------------------------------------------------------------------------
# The trace round trip
# --------------------------------------------------------------------------

def test_trace_survives_a_round_trip(repo):
    rec = TraceRecorder(week=4, case_id="T-01",
                        conditions=local_conditions("qwen3:4b-instruct",
                                                    prompt_version="v1"),
                        user_input="What does a parking vignette cost?")
    with rec.step("model", "qwen3:4b-instruct") as s:
        s.tokens(120, 30)
        s.detail(stop_reason="tool_use")
    with rec.step("tool", "search_services") as s:
        s.detail(query="parking vignette", hits=2)
    rec.finish(output="60 euros per year.", outcome="ok")

    loaded = read_traces()
    assert len(loaded) == 1
    t = loaded[0]
    assert t.case_id == "T-01"
    assert t.step_count == 2
    assert t.total_tokens == 150
    assert t.total_latency_ms >= 0
    assert [s.name for s in t.steps_of("tool")] == ["search_services"]
    # The conditions are not optional, which is the whole point.
    assert t.conditions.model == "qwen3:4b-instruct"
    assert t.conditions.settings["prompt_version"] == "v1"


def test_a_failing_step_is_recorded_before_the_exception_escapes(repo):
    rec = TraceRecorder(week=8, case_id="T-02",
                        conditions=local_conditions("qwen3:4b-instruct"),
                        user_input="anything")
    with pytest.raises(RuntimeError):
        with rec.step("tool", "flaky_search"):
            raise RuntimeError("upstream timeout")

    rec.finish(output=None, outcome="error")
    t = read_traces()[0]
    assert t.steps[0].ok is False
    assert "upstream timeout" in t.steps[0].detail["error"]


def test_a_malformed_trace_line_is_reported_with_its_line_number(repo):
    (repo / "artifacts").mkdir()
    (repo / "artifacts" / "traces.jsonl").write_text(
        '{"trace_id": "x", "week": 99}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="traces.jsonl:1"):
        read_traces()


# --------------------------------------------------------------------------
# The replay fixture
# --------------------------------------------------------------------------

def _fixture_file(path: Path, messages, content="60 euros per year."):
    key = call_key("qwen3:4b-instruct", messages, temperature=0.0)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "meta": {"model": "qwen3:4b-instruct", "recorded_at": "2026-08-10",
                 "planted_failures": ["case 3 invents a fee"]},
        "records": {key: {"response": {
            "choices": [{"finish_reason": "stop",
                         "message": {"content": content,
                                     "tool_calls": None}}],
            "usage": {"prompt_tokens": 120, "completion_tokens": 12},
        }}},
    }), encoding="utf-8")
    return path


def test_replay_answers_the_call_your_code_makes(tmp_path):
    messages = [{"role": "user", "content": "What does a vignette cost?"}]
    client = ReplayClient(_fixture_file(tmp_path / "replay.json", messages))

    reply = client.chat.completions.create(
        model="qwen3:4b-instruct", messages=messages, temperature=0.0)

    # Exactly the attribute path the real SDK gives you.
    assert reply.choices[0].message.content == "60 euros per year."
    assert reply.choices[0].finish_reason == "stop"
    assert reply.usage.prompt_tokens == 120
    assert client.hits == 1
    assert "planted" in client.describe() or "case 3" in client.describe()


def test_a_changed_prompt_misses_loudly_instead_of_silently(tmp_path):
    messages = [{"role": "user", "content": "What does a vignette cost?"}]
    client = ReplayClient(_fixture_file(tmp_path / "replay.json", messages))

    with pytest.raises(FixtureMiss) as exc:
        client.chat.completions.create(
            model="qwen3:4b-instruct", temperature=0.0,
            messages=[{"role": "user", "content": "a different question"}])
    assert "No recording for this call" in str(exc.value)


def test_repeated_sampling_replays_different_answers(tmp_path):
    """The same call three times must give the three recorded answers.

    Without this, every variance experiment in the course comes out
    unanimous by construction: week 1's temperature sweep, week 3's voting
    variant, and week 10's consistency at K would all silently measure the
    fixture rather than the model.
    """
    messages = [{"role": "user", "content": "pick a route"}]
    key = call_key("m", messages, temperature=0.7)
    path = tmp_path / "replay.json"
    path.write_text(json.dumps({
        "meta": {"model": "m"},
        "records": {key: {"responses": [
            {"choices": [{"message": {"content": r}, "finish_reason": "stop"}]}
            for r in ("info", "request", "info")
        ]}},
    }), encoding="utf-8")

    client = ReplayClient(path)
    got = [client.chat.completions.create(
        model="m", messages=messages, temperature=0.7
    ).choices[0].message.content for _ in range(3)]
    assert got == ["info", "request", "info"]

    # A fourth call cycles rather than raising, so a student who samples
    # more times than the fixture recorded still gets a plausible run.
    assert client.chat.completions.create(
        model="m", messages=messages, temperature=0.7
    ).choices[0].message.content == "info"
    assert client.sample_counts() == (1, 3)


def test_a_single_response_fixture_still_replays(tmp_path):
    """Older fixtures written before multi-sample must keep working."""
    messages = [{"role": "user", "content": "hello"}]
    client = ReplayClient(_fixture_file(tmp_path / "replay.json", messages))
    reply = client.chat.completions.create(
        model="qwen3:4b-instruct", messages=messages, temperature=0.0)
    assert reply.choices[0].message.content == "60 euros per year."


def test_a_students_own_prompt_still_replays_and_is_warned_about(tmp_path,
                                                                capsys):
    """Writing the prompt is the exercise, so replay must survive it.

    Without the looser fallback, the moment a student improves their system
    prompt every exact key changes and the whole recording stops matching,
    which makes replay useless in exactly the weeks that need it most.
    """
    recorded = [{"role": "system", "content": "the reference prompt"},
                {"role": "user", "content": "the heating is broken"}]
    path = tmp_path / "replay.json"
    key = call_key("m", recorded, temperature=0.0)
    path.write_text(json.dumps({
        "meta": {"model": "m"},
        "records": {key: {
            "request": {"model": "m", "messages": recorded},
            "responses": [{"choices": [{"message": {"content": "facilities"},
                                        "finish_reason": "stop"}]}],
        }},
    }), encoding="utf-8")

    client = ReplayClient(path)
    reply = client.chat.completions.create(
        model="m", temperature=0.0,
        messages=[{"role": "system", "content": "MY OWN much better prompt"},
                  {"role": "user", "content": "the heating is broken"}])

    assert reply.choices[0].message.content == "facilities"
    assert client.loose_hits == 1
    out = capsys.readouterr().out
    assert "your prompt differs" in out
    assert "not a measurement of your prompt" in out


def test_an_input_that_was_never_recorded_still_misses(tmp_path):
    """The loose fallback must not become a way to fabricate answers."""
    recorded = [{"role": "system", "content": "p"},
                {"role": "user", "content": "recorded input"}]
    path = tmp_path / "replay.json"
    path.write_text(json.dumps({
        "meta": {}, "records": {call_key("m", recorded, temperature=0.0): {
            "request": {"model": "m", "messages": recorded},
            "responses": [{"choices": [{"message": {"content": "x"}}]}],
        }}}), encoding="utf-8")

    with pytest.raises(FixtureMiss, match="none of them used this input"):
        ReplayClient(path).chat.completions.create(
            model="m", temperature=0.0,
            messages=[{"role": "user", "content": "an input nobody recorded"}])


def test_a_replayed_tool_call_can_be_put_back_into_the_message_list(tmp_path):
    """Every ReAct loop appends the assistant turn before the tool result.

    That means calling `model_dump()` on a replayed tool call. If replayed
    objects cannot do it, replay works for one step and breaks on the
    second, which is every week from 4 onward.
    """
    messages = [{"role": "user", "content": "what does it cost?"}]
    key = call_key("m", messages, temperature=0.0)
    path = tmp_path / "replay.json"
    path.write_text(json.dumps({
        "meta": {}, "records": {key: {
            "request": {"model": "m", "messages": messages},
            "responses": [{"choices": [{"finish_reason": "tool_calls",
                                        "message": {"content": None,
                                                    "tool_calls": [{
                                                        "id": "call_1",
                                                        "type": "function",
                                                        "function": {
                                                            "name": "search",
                                                            "arguments":
                                                                '{"q": "fee"}',
                                                        }}]}}]}],
        }}}), encoding="utf-8")

    reply = ReplayClient(path).chat.completions.create(
        model="m", messages=messages, temperature=0.0)
    call = reply.choices[0].message.tool_calls[0]
    assert call.function.name == "search"

    dumped = call.model_dump()
    assert dumped["function"]["name"] == "search"
    # It has to survive json round-tripping, because that is what happens
    # to it next.
    assert json.loads(json.dumps(dumped))["id"] == "call_1"


def test_the_key_ignores_things_that_do_not_change_the_answer():
    messages = [{"role": "user", "content": "hello"}]
    a = call_key("m", messages, temperature=0.0, stream=False, timeout=30)
    b = call_key("m", messages, temperature=0.0, stream=True)
    assert a == b
    c = call_key("m", messages, temperature=1.0)
    assert a != c


# --------------------------------------------------------------------------
# The handover fallback, which is what makes chaining survivable
# --------------------------------------------------------------------------

def test_the_handover_prefers_your_own_artifact(repo, tmp_path, capsys):
    lab = repo / "labs" / "week10_evaluation_harness"
    (lab / "fixtures" / "reference").mkdir(parents=True)
    (lab / "fixtures" / "reference" / "goldset.json").write_text(
        json.dumps({"schema_version": SCHEMA_VERSION, "cases": []}),
        encoding="utf-8")

    mine = GoldSet(cases=[GoldCase(case_id="Q01", week_added=7,
                                   question="mine",
                                   expected_behavior="answers")])
    write_json("artifacts/goldset.json", mine)

    data, source = load_or_reference("goldset.json",
                                     lab="week10_evaluation_harness")
    assert source == "own"
    assert data["cases"][0]["question"] == "mine"


def test_the_handover_falls_back_and_says_so(repo, capsys):
    lab = repo / "labs" / "week10_evaluation_harness"
    (lab / "fixtures" / "reference").mkdir(parents=True)
    (lab / "fixtures" / "reference" / "goldset.json").write_text(
        json.dumps({"schema_version": SCHEMA_VERSION,
                    "cases": [{"case_id": "Q01", "week_added": 7,
                               "question": "reference",
                               "expected_behavior": "answers"}]}),
        encoding="utf-8")

    data, source = load_or_reference("goldset.json",
                                     lab="week10_evaluation_harness")
    assert source == "reference"
    assert "Record this in DECISIONS.md" in capsys.readouterr().out


# --------------------------------------------------------------------------
# The verifier
# --------------------------------------------------------------------------

def test_verify_passes_on_a_clean_repository(repo, capsys):
    rec = TraceRecorder(week=1, case_id="C-01",
                        conditions=local_conditions("qwen3:4b-instruct"),
                        user_input="hello")
    with rec.step("model", "qwen3:4b-instruct") as s:
        s.tokens(10, 5)
    rec.finish(output="hi", outcome="ok")

    assert verify_main(repo) == 0
    assert "All artifacts match" in capsys.readouterr().out


def test_verify_catches_a_broken_trace_and_names_the_field(repo, capsys):
    (repo / "artifacts").mkdir()
    bad = {"trace_id": "x", "week": 4, "case_id": "C", "started_at": "now",
           "conditions": {"model": "m", "temperature": 0.0,
                          "run_date": "2026-08-10"},
           "input": "i", "steps": [], "output": None,
           "outcome": "definitely_fine"}          # not a valid Outcome
    (repo / "artifacts" / "traces.jsonl").write_text(
        json.dumps(bad) + "\n", encoding="utf-8")

    assert verify_main(repo) == 1
    out = capsys.readouterr().out
    assert "FAIL" in out and "outcome" in out


def test_verify_refuses_a_finding_that_claims_a_fix_with_no_test(repo,
                                                                capsys):
    (repo / "artifacts").mkdir()
    (repo / "artifacts" / "findings.json").write_text(json.dumps([{
        "finding_id": "F-01", "owasp_class": "LLM01", "severity": "high",
        "channel": "retrieved passage", "blast_radius": "sent an email",
        "reproduction": "run 02_probe.py --case F-01",
        "mitigation": "added an allow list at the gateway",
        "regression_test": None, "accepted_residual": False,
    }]), encoding="utf-8")

    assert verify_main(repo) == 1
    assert "no regression test" in capsys.readouterr().out


# --------------------------------------------------------------------------
# Cost estimates stay labeled as estimates
# --------------------------------------------------------------------------

def test_an_estimate_says_it_is_an_estimate():
    e = estimate(input_tokens=1_000_000, output_tokens=100_000, tier="mid")
    assert e.total == pytest.approx(2.50 + 1.00)
    # Reported per thousand calls, because one call is always about
    # nothing and quoting that number teaches nobody anything.
    assert e.per_thousand == pytest.approx(3500.0)
    assert "per thousand calls" in e.summary()
    assert "Estimate, not a measurement" in e.summary()
    assert "2026-08-10" in e.summary()
