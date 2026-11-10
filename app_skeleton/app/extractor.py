"""Stage: structured extraction. Replaced in week 2.

The week 2 extractor turns a free-text message into a validated
`ServiceRequest`. Until you wire yours in, this stub refuses: it returns no
record, and the pipeline answers that nothing was logged.

To replace it, copy your `labs/week02/starter/extractor.py` over this file
and set `SYSTEM` to the prompt your DECISIONS.md chose, zero-shot or
few-shot. Keep these names and signatures, because `pipeline.py` calls them:

    ServiceRequest                        category, urgency, due_date, quote
    SYSTEM: str                           the system prompt you ship
    extract(client, system, document_text, model=SMALL.name)
        -> tuple[ServiceRequest | None, dict]
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from project.models import SMALL

from .stub import stub

PROMPT_VERSION = "stub"
SYSTEM = ""


class ServiceRequest(BaseModel):
    """The week 2 record. Your own version carries the field descriptions."""

    category: Literal["access", "hardware", "billing", "facilities", "other"]
    urgency: Literal["urgent", "standard", "info"]
    due_date: str | None = None
    quote: str


@stub(week=2, does="refuses: returns no record, so nothing is logged")
def extract(client, system: str, document_text: str,
            model: str = SMALL.name) -> tuple[ServiceRequest | None, dict]:
    return None, {"seconds": 0.0, "prompt_tokens": 0,
                  "completion_tokens": 0, "raw": "",
                  "error": "stub: the week 2 extractor is not wired in"}
