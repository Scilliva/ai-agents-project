"""The model boundary for week 9, and the guard that makes it honest.

One call reads one GROUP of at most three fields from one image. That is not
a stylistic choice. Six fields in a single call fails three different ways on
this model, all of them silently, and `WEEK09_FINDINGS.md` has the numbers.

The important function in this file is `guard`. Every failure this model
produces arrives as a normal 200 response with `done_reason: stop`, so if you
only catch exceptions you will catch nothing at all.
"""

from __future__ import annotations

import base64
import io
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from perturb import apply_variant

MODEL = "qwen3-vl:4b"
ENDPOINT = "http://127.0.0.1:11434/api/chat"
TIMEOUT_S = 300

SYSTEM = (
    "You read Luxembourg invoices. Return each requested field exactly as it "
    "is printed on the page, as a string, including any spaces used as "
    "thousands separators. If a field is NOT PRESENT on the page, return null "
    "for it. Never guess a value that is not printed."
)


@dataclass
class VisionResult:
    """One call. `failure` is None only when the result is usable."""

    doc: str
    group: str
    variant: str
    fields: dict[str, str | None] = field(default_factory=dict)
    failure: str | None = None
    elapsed_s: float = 0.0
    prompt_tokens: int = 0
    output_tokens: int = 0
    done_reason: str = ""
    raw_content: str = ""

    @property
    def ok(self) -> bool:
        return self.failure is None


def encode(path: Path, variant: str = "clean") -> str:
    """Base64 PNG of the image after one named degradation."""
    buf = io.BytesIO()
    apply_variant(path, variant).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def flat_schema(fields: list[str]) -> dict:
    """Flat, nullable, and required. Nested schemas fail on this model."""
    return {"type": "object",
            "properties": {f: {"type": ["string", "null"]} for f in fields},
            "required": list(fields)}


# --------------------------------------------------------------------------
# TODO 1, answered. Three silent failures, none of them an exception.
# --------------------------------------------------------------------------

def guard(content: str, thinking: str, done_reason: str,
          fields: list[str]) -> tuple[dict | None, str | None]:
    """TODO 1. Return (parsed_fields, failure_reason).

    This is the most important function in the lab, because every failure
    this model produces arrives as a normal HTTP 200, and two of the three
    arrive with `done_reason: stop`, which is the API saying nothing went
    wrong. If you only catch exceptions you will catch nothing.

    Return (None, "some reason") for each of these, and (fields, None) only
    when the result is genuinely usable:

      a) done_reason == "length". The thinking ran until the context ran
         out and the answer never came. done_reason is the ONLY signal.
      b) content is empty or whitespace. Seen when `think=False` is passed:
         the JSON goes into `thinking` instead, with every value "".
         Mention `thinking` in your reason if it is non-empty, because that
         is the clue that tells the next reader what happened.
      c) content does not parse as JSON, or parses to something that is not
         an object. The model can emit a valid JSON prefix and then drift
         back into prose inside a string value.
      d) a required key from `fields` is missing.
      e) every value is None or a blank string. THIS is the one that a
         naive check passes: the object parsed, the keys are all present,
         and it tells you nothing at all. Refusing it here is the
         difference between a check and a formality.

    Run `python -m pytest ../tests` or the self-test at the bottom of this
    file: it feeds guard() each of these on purpose and expects a refusal.
    A guard that accepts them all is worth nothing.
    """
    raise NotImplementedError("TODO 1: guard")


# --------------------------------------------------------------------------
# TODO 2, answered. The call itself.
# --------------------------------------------------------------------------

def read_group(image_path: Path, group: str, fields: list[str],
               variant: str = "clean", replay: "Fixture | None" = None,
               record: "Fixture | None" = None,
               system: str | None = None, prompt: str | None = None
               ) -> VisionResult:
    """Read one group of fields from one image.

    Note what is NOT passed: `think`. Leaving thinking on is what makes this
    model read correctly, and passing `think=False` returns blanks. That is
    measured, not assumed.
    """
    doc = image_path.stem
    if replay is not None:
        hit = replay.get(doc, group, variant)
        if hit is not None:
            return hit

    # TODO 2. Build and send the request, then hand the response to guard.
    #
    #   POST to ENDPOINT with json:
    #     model    MODEL
    #     stream   False
    #     format   flat_schema(fields)          <- structured output
    #     options  {"temperature": 0.0}
    #     messages a system message (`system or SYSTEM`) and a user message
    #              carrying "images": [encode(image_path, variant)] plus
    #              `prompt` or a default naming the fields you want.
    #
    # Do NOT pass "think": False. It makes the call several times faster and
    # returns an object whose every value is an empty string. That is
    # measured, not folklore, and it is in WEEK09_FINDINGS.md.
    #
    # Wrap the call so a transport failure returns a VisionResult with a
    # `failure` set rather than raising, then build the VisionResult with
    # the token counts and done_reason from the response, because block 2
    # needs them.
    raise NotImplementedError("TODO 2: read_group")

    if record is not None:
        record.put(out)
    return out


def read_naive(image_path: Path, fields: list[str], variant: str = "clean",
               replay: "Fixture | None" = None,
               record: "Fixture | None" = None) -> VisionResult:
    """The obvious implementation: ask for all six fields in one call.

    This is here to be run and compared, not to be used. It is what everyone
    writes first, it is what the lecture's example looks like, and on this
    model it fails three ways that a naive caller reports as success. Block 2
    runs it beside `read_group` so the difference is a number rather than an
    assertion.
    """
    return read_group(image_path, "naive", fields, variant=variant,
                      replay=replay, record=record)


# --------------------------------------------------------------------------
# Replay. Vision calls are slow, so a recorded run is what makes the lab
# fit in ninety minutes. Keyed on what varies: doc, group, variant.
# --------------------------------------------------------------------------

class Fixture:
    """A recorded set of vision calls, keyed by (doc, group, variant)."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.entries: dict[str, dict] = {}
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    row = json.loads(line)
                    self.entries[self._key(row["doc"], row["group"],
                                           row["variant"])] = row

    @staticmethod
    def _key(doc: str, group: str, variant: str) -> str:
        return f"{doc}|{group}|{variant}"

    def get(self, doc: str, group: str, variant: str) -> VisionResult | None:
        row = self.entries.get(self._key(doc, group, variant))
        if row is None:
            return None
        return VisionResult(**{k: v for k, v in row.items()
                               if k in VisionResult.__dataclass_fields__})

    def has(self, doc: str, group: str, variant: str) -> bool:
        return self._key(doc, group, variant) in self.entries

    def put(self, result: VisionResult) -> None:
        row = {"doc": result.doc, "group": result.group,
               "variant": result.variant,
               "fields": result.fields, "failure": result.failure,
               "elapsed_s": round(result.elapsed_s, 2),
               "prompt_tokens": result.prompt_tokens,
               "output_tokens": result.output_tokens,
               "done_reason": result.done_reason,
               "raw_content": result.raw_content}
        self.entries[self._key(result.doc, result.group,
                               result.variant)] = row
        # Appended immediately rather than at the end, so a run that is
        # interrupted keeps everything it already paid for.
        with self.path.open("a") as fh:
            fh.write(json.dumps(row) + "\n")


def find_fixture(name: str = "vision_runs.jsonl") -> Path:
    """Look where the lab is, then where the student copied the script."""
    here = Path(__file__).resolve()
    for base in (here.parent, here.parent.parent, Path.cwd(),
                 Path.cwd().parent):
        candidate = base / "fixtures" / name
        if candidate.exists():
            return candidate
    return here.parent.parent / "fixtures" / name
