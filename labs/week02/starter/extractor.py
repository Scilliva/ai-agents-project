"""The schema and the call. Two TODO markers.

A prompt is not a string you tweak until the output looks nice. It is a
versioned artifact with a specification inside it, and the specification is
the part that has to be written down: what each field means, what the
allowed values are, and what to do when the message does not say.

Everything you write here is the specification. The scorer in `scoring.py`
is what tells you whether the model read it the way you meant it.
"""

from __future__ import annotations

import json
import time
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from project.models import BASE_URL, API_KEY, SMALL

PROMPT_VERSION = "week02-zero-shot-v1"


# --------------------------------------------------------------------------
# TODO 1. Finish the schema.
# --------------------------------------------------------------------------

class ServiceRequest(BaseModel):
    """One extracted record.

    Two fields are done. Finish the other two, and pay attention to what the
    types say, because the type is half of your specification and the model
    is shown it.

    due_date: the message may state a calendar date in any format or
        language, may state a relative expression such as "before the end of
        the month", or may state nothing. Only one of those three is a date.
        What Python type expresses "a date, or explicitly no date"? Note that
        `str` cannot, and that the difference between `None` and `""` and
        `"none"` will cost you marks in the scorer if you are casual about it.

    quote: a span copied verbatim out of the message that supports your
        urgency decision. It is scored by substring search against the source,
        for free, with no model involved. That makes it the most valuable
        field on this schema and the reason it is here.
    """

    category: Literal["access", "hardware", "billing", "facilities", "other"]
    urgency: Literal["urgent", "standard", "info"]

    # TODO 1a: due_date. Give it a type that can hold a date or nothing,
    #          and a Field(description=...) stating the convention. The
    #          description is sent to the model, so it is prompt engineering
    #          rather than documentation.
    # TODO 1b: quote. A string, with a description that says "verbatim" in
    #          words a model will act on. Consider a max_length.


# --------------------------------------------------------------------------
# TODO 2. Build the messages.
# --------------------------------------------------------------------------

SYSTEM_ZERO_SHOT = """\
TODO 2a: write the system prompt.

It has to state, in words a model will follow:
  - what the job is
  - that messages arrive in English, French, or German
  - the allowed values for category and for urgency
  - the due_date convention, including what counts as "no date"
  - that quote must be copied character for character, not translated

Write the conventions here even though they are also in the schema. The
schema constrains the shape of the answer. The prompt is what tells the
model how to decide. Neither one does the other's job.
"""


def build_messages(system: str, document_text: str) -> list[dict]:
    """TODO 2b. Return the message list for one document.

    Two messages, and the split matters. The system message carries the
    instruction, which is the same for every document. The user message
    carries the document, which changes every time.

    A common first attempt concatenates them into one user message. It
    works, and then in week 12 you find out why it was a bad habit: if the
    instruction and the data are in the same place, a document that contains
    an instruction is indistinguishable from your instruction.
    """
    raise NotImplementedError("TODO 2b: return the two messages")


# --------------------------------------------------------------------------
# Given. The call, the validation, and the timing.
# --------------------------------------------------------------------------

_REQUIRED_FIELDS = {"category", "urgency", "due_date", "quote"}


def _check_schema_is_finished() -> None:
    """Fail with the marker number rather than with an AttributeError.

    Without this, a schema missing `due_date` produces a crash three files
    away in the scorer, which is a bad way to find out you skipped TODO 1.
    """
    missing = _REQUIRED_FIELDS - set(ServiceRequest.model_fields)
    if missing:
        raise NotImplementedError(
            f"TODO 1: the schema is still missing {sorted(missing)}. "
            f"Finish ServiceRequest in extractor.py before running this. "
            f"The scorer needs all four fields.")


def extract(client, system: str, document_text: str,
            model: str = SMALL.name) -> tuple[ServiceRequest | None, dict]:
    """One document in, one validated record out, plus what it cost.

    Note the two layers. The endpoint is asked to honor the schema, and then
    the answer is validated anyway. Week 1 said a single run is a sample.
    This is the same idea applied to a contract: an output that claims to
    match a schema is a claim, and claims get checked.

    Returns (record or None, meta). A None record means validation failed,
    and `meta["error"]` says how. That is a result, not a crash, because in
    block 2 you need to count how often it happens.
    """
    _check_schema_is_finished()
    t0 = time.perf_counter()
    reply = client.chat.completions.create(
        model=model,
        temperature=0.0,
        max_tokens=300,
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "service_request",
                            "schema": ServiceRequest.model_json_schema()},
        },
        messages=build_messages(system, document_text),
    )
    raw = reply.choices[0].message.content
    meta = {
        "seconds": time.perf_counter() - t0,
        "prompt_tokens": reply.usage.prompt_tokens,
        "completion_tokens": reply.usage.completion_tokens,
        "raw": raw,
        "error": None,
    }
    try:
        return ServiceRequest.model_validate_json(raw), meta
    except ValidationError as exc:
        meta["error"] = str(exc).splitlines()[0]
        return None, meta


def get_client(replay: bool):
    """The real client, or the recording. Same surface either way."""
    if replay:
        from project.fixtures import ReplayClient
        client = ReplayClient.from_lab("week02_prompting_and_extraction")
        print(f"replay: {client.describe()}\n")
        return client
    from openai import OpenAI
    return OpenAI(base_url=BASE_URL, api_key=API_KEY)


def run_variant(client, system: str, label: str, docs, golds):
    """Extract every document, record a trace each, and score.

    Shared by the zero-shot and the few-shot runners so that the two
    variants genuinely go through the same code. If you find yourself
    copying this function to change one thing for one variant, stop: that is
    how a comparison quietly stops being a comparison.
    """
    from scoring import score_all
    from project.trace import TraceRecorder, local_conditions

    records, metas = [], []
    for doc in docs:
        rec = TraceRecorder(
            week=2, case_id=doc.id,
            conditions=local_conditions(SMALL.name, temperature=0.0,
                                        prompt_version=PROMPT_VERSION,
                                        variant=label, language=doc.lang),
            user_input=doc.text)
        with rec.step("model", SMALL.name) as step:
            record, meta = extract(client, system, doc.text)
            step.tokens(meta["prompt_tokens"], meta["completion_tokens"])
            step.detail(valid=record is not None, error=meta["error"])
        rec.finish(output=meta["raw"], outcome="ok" if record else "error")
        records.append(record)
        metas.append(meta)

    board = score_all(records, golds, docs)
    tok = sum(m["prompt_tokens"] + m["completion_tokens"] for m in metas)
    secs = sum(m["seconds"] for m in metas)
    print(f"{label}: {board.as_counts()}   invalid {board.invalid}")
    print(f"  {tok} tokens, {secs:.1f}s over {len(docs)} documents\n")
    return board, records, metas
