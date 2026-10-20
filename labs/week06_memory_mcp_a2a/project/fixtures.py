"""Replay fixtures, and the fallback when a handover is missing.

Two separate jobs live here, and they solve two separate problems.

**Replay.** A recorded model response, keyed by exactly what you sent. It
lets you test your own logic in under a second with no server and no
waiting, and it makes a checkpoint discussion possible, because everybody in
the room is looking at the same output rather than at their own private
sample. Every session in this course that calls a model ships one.

The fixtures deliberately contain failures. A recording where every check
passes teaches you nothing. If your checks pass on every case in the
fixture, that is not a good result, it means your checks do not do anything,
and the checklist for the week will say so.

**Reference artifacts.** The handover safety net. Week 7 writes a gold set
that week 10 reads. If you missed week 7, or your file is broken, you load
the reference copy shipped with week 10 instead and you write down that you
did. Your reasoning is still yours. Only the input is borrowed.

Usage, replay:

    from project.fixtures import ReplayClient
    client = ReplayClient.from_lab("week04_react_tool_use")
    reply = client.chat.completions.create(model=..., messages=[...])

Usage, handover:

    from project.fixtures import load_or_reference
    goldset, source = load_or_reference("goldset.json", lab="week10_...")
    print(f"gold set loaded from: {source}")   # 'own' or 'reference'
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .trace import repo_root


class FixtureMiss(KeyError):
    """The fixture has no recording for this call.

    Raised loudly rather than falling through to a live call, because a
    replay run that silently starts spending time and memory is a replay run
    you cannot trust to be reproducible.
    """


# --------------------------------------------------------------------------
# Keying a call
# --------------------------------------------------------------------------

def call_key(model: str, messages: list[dict[str, Any]],
             **params: Any) -> str:
    """A stable fingerprint of one model call.

    Only the fields that change the answer are in the key. `stream` and
    timeouts are not, so a recording made without streaming replays for code
    that asked for it.
    """
    keyed = {
        "model": model,
        "messages": messages,
        "temperature": params.get("temperature"),
        "tools": params.get("tools"),
        "response_format": params.get("response_format"),
        "max_tokens": params.get("max_tokens") or params.get(
            "max_completion_tokens"),
    }
    blob = json.dumps(keyed, sort_keys=True, ensure_ascii=False,
                      default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def input_key(model: str, messages: list[dict[str, Any]]) -> str:
    """A looser fingerprint: this model, on this input, whatever the prompt.

    The exact key above includes the system prompt, which is correct and
    also inconvenient, because in most of these labs writing the system
    prompt is the exercise. The moment you improve your prompt, every exact
    key changes and the recording stops matching.

    So there is a second index, on the model and the user message only. It
    lets you develop a scorer, a policy layer, or a check against recorded
    answers while your own prompt is still changing. What comes back is the
    reference prompt's answer to your document, not your prompt's answer,
    and `ReplayClient` says so out loud the first time it happens.

    Use it for building the machinery around the model. Never quote a number
    produced this way as a measurement of your own prompt.
    """
    last_user = next((m.get("content", "") for m in reversed(messages)
                      if m.get("role") == "user"), "")
    blob = json.dumps({"model": model, "user": last_user},
                      sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


# --------------------------------------------------------------------------
# Replaying a recording with the shape the OpenAI SDK returns
# --------------------------------------------------------------------------

class _Obj:
    """Attribute access over a dict, so replayed objects read like real ones.

    It also answers `model_dump()`, because the real SDK returns pydantic
    models and every agent loop calls that to put a tool call back into the
    message list. Without it, replay works right up until the first loop
    that takes a second step, which is every week from 4 onward.
    """

    def __init__(self, data: Any):
        self._data = data
        if isinstance(data, dict):
            for k, v in data.items():
                setattr(self, k, _wrap(v))

    def model_dump(self, *args: Any, **kwargs: Any) -> Any:
        return self._data

    def __repr__(self) -> str:
        return f"_Obj({self._data!r})"


def _wrap(value: Any) -> Any:
    if isinstance(value, dict):
        return _Obj(value)
    if isinstance(value, list):
        return [_wrap(v) for v in value]
    return value


class _Completions:
    def __init__(self, owner: "ReplayClient"):
        self._owner = owner

    def create(self, *, model: str, messages: list[dict[str, Any]],
               **params: Any):
        key = call_key(model, messages, **params)
        record = self._owner.records.get(key)

        if record is None:
            # Your prompt is not the reference prompt, which is expected:
            # writing it is the exercise. Fall back to the reference answer
            # for this same input, and warn once so nobody quotes the number
            # as a measurement of their own prompt.
            loose = self._owner._by_input.get(input_key(model, messages))
            if loose is not None:
                record = self._owner.records[loose]
                self._owner.loose_hits += 1
                if not self._owner._warned_loose:
                    self._owner._warned_loose = True
                    print(
                        "  note: your prompt differs from the one this "
                        "fixture was recorded with, so replay is returning\n"
                        "        the reference prompt's answer for each "
                        "input. That is fine for developing a scorer or a\n"
                        "        policy layer. It is not a measurement of "
                        "your prompt: run without --replay for that.")

        if record is None:
            raise FixtureMiss(
                f"No recording for this call (key {key}, model {model}).\n"
                f"The fixture has {len(self._owner.records)} recordings, and "
                f"none of them used this input either.\n"
                f"Either the model name is wrong, or you changed the input "
                f"text, or you are meant to run this one live.\n"
                f"Fixture: {self._owner.path}")
        self._owner.hits += 1

        # A key can hold more than one recording, because the same call made
        # twice at a non-zero temperature is two different answers and both
        # are worth replaying. Repeated calls walk the list in order and
        # then cycle. Without this, sampling the same prompt three times in
        # replay would return one answer three times, and every experiment
        # about variance would come out unanimous by construction.
        responses = record.get("responses")
        if responses is None:
            return _wrap(record["response"])
        i = self._owner._cursor.get(key, 0)
        self._owner._cursor[key] = i + 1
        return _wrap(responses[i % len(responses)])


class _Chat:
    def __init__(self, owner: "ReplayClient"):
        self.completions = _Completions(owner)


class ReplayClient:
    """A stand in for the OpenAI client that answers from a recording.

    It is deliberately not a subclass of anything. If your code works
    against this, it works against the real client, because the only surface
    it offers is the one the labs use.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(
                f"No fixture at {self.path}. Every lab that calls a model "
                f"ships one in its fixtures/ directory.")
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.meta: dict[str, Any] = payload.get("meta", {})
        self.records: dict[str, Any] = payload["records"]
        self.hits = 0
        self.loose_hits = 0
        self._cursor: dict[str, int] = {}
        self._warned_loose = False

        # Secondary index: model plus user message, ignoring the system
        # prompt. First recording for a given input wins, which makes the
        # fallback deterministic.
        self._by_input: dict[str, str] = {}
        for k, rec in self.records.items():
            req = rec.get("request") or {}
            if not req.get("messages"):
                continue
            ik = input_key(req.get("model", ""), req["messages"])
            self._by_input.setdefault(ik, k)

        self.chat = _Chat(self)

    @classmethod
    def from_lab(cls, lab: str, name: str = "replay.json") -> "ReplayClient":
        """Load the fixture shipped with a lab folder."""
        return cls(_lab_dir(lab) / "fixtures" / name)

    def sample_counts(self) -> tuple[int, int]:
        """(distinct calls, total recorded responses)."""
        total = sum(len(r["responses"]) if "responses" in r else 1
                    for r in self.records.values())
        return len(self.records), total

    def describe(self) -> str:
        return (f"{len(self.records)} recordings, model "
                f"{self.meta.get('model', 'unknown')}, recorded "
                f"{self.meta.get('recorded_at', 'unknown')}. "
                f"Deliberate failures: "
                f"{', '.join(self.meta.get('planted_failures', [])) or 'none'}")


class RecordingClient:
    """Wraps a real client and writes every call into a fixture.

    Used to build the fixtures shipped with the labs. You do not need it to
    complete a session, but it is how you make your own replay fixture for
    your project, and week 10 suggests exactly that.
    """

    def __init__(self, inner: Any, path: str | Path, **meta: Any):
        self.inner = inner
        self.path = Path(path)
        self.meta = meta
        self.records: dict[str, Any] = {}
        if self.path.exists():
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            self.records = payload.get("records", {})
        self.chat = _RecChat(self)

    def save(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"meta": self.meta, "records": self.records},
                       indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        return self.path


class _RecChat:
    def __init__(self, owner: RecordingClient):
        self.completions = _RecCompletions(owner)


class _RecCompletions:
    def __init__(self, owner: RecordingClient):
        self._owner = owner

    def create(self, *, model: str, messages: list[dict[str, Any]],
               **params: Any):
        reply = self._owner.inner.chat.completions.create(
            model=model, messages=messages, **params)
        key = call_key(model, messages, **params)
        payload = (reply.model_dump() if hasattr(reply, "model_dump")
                   else reply)
        slot = self._owner.records.setdefault(key, {
            "request": {"model": model, "messages": messages, **params},
            "responses": [],
        })
        # Append rather than overwrite. Calling the same prompt three times
        # at temperature 0.7 is three recordings, not one, and the whole
        # point of recording it is that the three differ.
        slot.setdefault("responses", []).append(payload)
        return reply


# --------------------------------------------------------------------------
# Handover fallback
# --------------------------------------------------------------------------

def _lab_dir(lab: str) -> Path:
    """Find a lab folder, whether you are in the course repo or your own.

    The course folder keeps the long name (`week04_react_tool_use`); the
    brief has you unpack each week as `labs/week04`. Both are tried, long
    name first.
    """
    names = [lab]
    short = lab.split("_", 1)[0]
    if short != lab:
        names.append(short)
    for base in (repo_root() / "labs", repo_root()):
        for name in names:
            candidate = base / name
            if candidate.exists():
                return candidate
    raise FileNotFoundError(
        f"Cannot find the lab folder {lab!r} (or {short!r}) under "
        f"{repo_root() / 'labs'}.")


def find_fixture(name: str, script: str, lab: str | None = None) -> Path:
    """Locate a fixture no matter where you copied the script to.

    You will move these scripts. The brief tells you to copy a lab into
    `labs/weekNN/` in your own repository, people reorganize, and a hard
    coded `../fixtures` breaks the moment anybody does. So this looks in the
    places a fixture can reasonably be, in order, and fails with all of them
    listed rather than with just the last one.

    Pass `script` as `__file__` from the calling script.

        FIXTURE = find_fixture("reference_runs.json", __file__,
                               lab="week01_setup_and_first_call")
    """
    override = os.environ.get("COURSE_FIXTURES")
    here = Path(script).resolve().parent

    candidates = [
        here / "fixtures" / name,           # script sits beside fixtures/
        here.parent / "fixtures" / name,    # script in starter/ or solution/
        repo_root() / "fixtures" / name,
    ]
    if override:
        candidates.insert(0, Path(override) / name)
    if lab:
        try:
            candidates.append(_lab_dir(lab) / "fixtures" / name)
        except FileNotFoundError:
            pass

    for path in candidates:
        if path.exists():
            return path

    listed = "\n".join(f"    {p}" for p in candidates)
    raise FileNotFoundError(
        f"Could not find the fixture {name!r}. Looked in:\n{listed}\n\n"
        f"Fixtures ship with the lab. Copy the whole lab folder, including "
        f"its fixtures/ directory, or set COURSE_FIXTURES to point at it.")


def load_or_reference(artifact: str, lab: str,
                      artifact_dir: str = "artifacts") -> tuple[Any, str]:
    """Load your own artifact, or the shipped reference one.

    Returns `(data, source)` where source is `'own'` or `'reference'`. The
    checklist for the week asks you to record which, and it matters: a
    result computed on the reference gold set is a result about the
    reference pipeline, not about yours.
    """
    own = repo_root() / artifact_dir / artifact
    if own.exists() and own.stat().st_size > 0:
        return _read(own), "own"

    ref = _lab_dir(lab) / "fixtures" / "reference" / artifact
    if not ref.exists():
        raise FileNotFoundError(
            f"Neither your own {own} nor the reference copy {ref} exists.")
    print(f"  note: {artifact} not found at {own}, using the reference copy "
          f"shipped with {lab}. Record this in DECISIONS.md.")
    return _read(ref), "reference"


def _read(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return json.loads(text)
