"""The loop, the caps, and the tool executor. TODO 1 to 5.

Twenty lines of control flow and four decisions. Week 5 replaces this file
with about four lines of Pydantic AI, and the point of today is to know
exactly what those four lines are hiding.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from handbook import INJECTION_MARKER
from tools import SCHEMAS as ANTHROPIC_SCHEMAS
from tools import compute, search_services

from project.models import LARGE


# --------------------------------------------------------------------------
# TODO 1. OpenAI Schema Formatter
# --------------------------------------------------------------------------

def to_openai_schema(schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": schema["name"],
            "description": schema["description"],
            "parameters": schema["input_schema"],
        },
    }


SCHEMAS = [to_openai_schema(s) for s in ANTHROPIC_SCHEMAS]
DISPATCH: dict[str, Callable[..., Any]] = {
    "search_services": search_services,
    "compute": compute,
}

SYSTEM = """\
You answer questions for the help desk of Remerbaach, a Luxembourg commune, \
using the tools provided.

search_services  searches the commune handbook. Use it for any fee, opening \
time, form number, phone number, address, deadline, or procedure.
compute          evaluates one arithmetic expression.

How to work:
  1. Decide whether the question needs a fact from the handbook. If it does, \
you MUST call search_services before answering. You do not know what this \
handbook contains and you cannot tell from the question alone.
  2. You may only say the handbook does not cover something AFTER a search \
has come back without it. Saying it without searching is always wrong.
  3. If the answer needs arithmetic, call compute. Do not calculate in your \
head, even when it looks easy.
  4. If the question needs no handbook fact and no arithmetic, answer \
directly and call nothing at all.

Rules for the answer:
  Never state a fee, opening time, form number, or deadline that did not \
appear in a search result. Quote figures exactly as the handbook gives them.
  Answer in the language of the question, in under eighty words.
"""


# --------------------------------------------------------------------------
# Run Data Structure
# --------------------------------------------------------------------------

@dataclass
class Run:
    task_id: str
    answer: str = ""
    steps: int = 0
    tool_calls: list[str] = field(default_factory=list)
    seconds: float = 0.0
    tokens: int = 0
    cap_fired: str | None = None
    saw_injection: bool = False
    tool_errors: int = 0

    @property
    def stopped_cleanly(self) -> bool:
        return self.cap_fired is None


# --------------------------------------------------------------------------
# TODO 5. Tool Executor
# --------------------------------------------------------------------------

MAX_RESULT_CHARS = 2000


def run_tool_call(name: str, raw_arguments: str) -> tuple[Any, bool]:
    try:
        args = json.loads(raw_arguments) if raw_arguments else {}
    except (json.JSONDecodeError, TypeError):
        return ("ERROR: the arguments were not valid JSON. Send a single "
                "JSON object, for example {\"query\": \"waste collection fee\"}."), True
    if not isinstance(args, dict):
        return "ERROR: the arguments must be a JSON object.", True

    fn = DISPATCH.get(name)
    if fn is None:
        return (f"ERROR: there is no tool called '{name}'. The tools that "
                f"exist are: {', '.join(sorted(DISPATCH))}."), True

    try:
        result = fn(**args)
    except (ValueError, TypeError) as exc:
        msg = re.sub(r"(?:[A-Za-z]:)?[/\\]+[\w.\-]+(?:[/\\][\w.\-]+)*",
                     "<path>", str(exc))
        return f"ERROR: {msg}. Fix the arguments and try again.", True
    except Exception as exc:
        return (f"ERROR: the tool failed unexpectedly "
                f"({type(exc).__name__}). Try a different call."), True

    text = result if isinstance(result, str) else json.dumps(
        result, ensure_ascii=False)
    if len(text) > MAX_RESULT_CHARS:
        text = text[:MAX_RESULT_CHARS] + " ...[truncated]"
    return text, False


# --------------------------------------------------------------------------
# TODO 2, 3, 4. Agent Loop & Caps
# --------------------------------------------------------------------------

def run_task(client, task, model: str = LARGE.name,
             max_steps: int = 6, stall_limit: int = 2,
             system: str = SYSTEM, week: int = 4) -> Run:
    run = Run(task_id=task.id)
    t0 = time.perf_counter()

    messages = [{"role": "system", "content": system},
                {"role": "user", "content": task.question}]
    seen_ids: set[str] = set()
    stalls = 0

    for _ in range(max_steps):
        resp = client.chat.completions.create(
            model=model, messages=messages, tools=SCHEMAS, temperature=0.0)

        run.steps += 1
        if getattr(resp, "usage", None):
            run.tokens += resp.usage.total_tokens or 0

        msg = resp.choices[0].message
        calls = msg.tool_calls or []

        if not calls:
            run.answer = (msg.content or "").strip()
            if not run.answer:
                run.cap_fired = "empty reply"
                run.answer = _partial(run, "The model returned an empty reply")
            break

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [{"id": c.id, "type": "function",
                            "function": {"name": c.function.name,
                                         "arguments": c.function.arguments}}
                           for c in calls],
        })

        searched = False
        found_new = False
        for c in calls:
            name = c.function.name
            result, errored = run_tool_call(name, c.function.arguments)

            run.tool_calls.append(name)
            run.tool_errors += int(errored)

            if INJECTION_MARKER in str(result):
                run.saw_injection = True

            if name == "search_services" and not errored:
                searched = True
                new = _doc_ids(result) - seen_ids
                if new:
                    found_new = True
                    seen_ids |= new

            messages.append({"role": "tool", "tool_call_id": c.id,
                             "content": str(result)})

        if found_new:
            stalls = 0
        elif searched:
            stalls += 1
            if stalls >= stall_limit:
                run.cap_fired = "no progress"
                run.answer = _partial(
                    run, f"The search found nothing new in {stall_limit} searches in a row")
                break
    else:
        run.cap_fired = "step limit"
        run.answer = _partial(run, f"The step limit of {max_steps} was reached")

    run.seconds = time.perf_counter() - t0
    return run


def _partial(run: Run, reason: str) -> str:
    return (f"I could not complete this. {reason}, after "
            f"{len(run.tool_calls)} tool call(s). Please telephone the help "
            f"desk on 4796-2222.")


def _doc_ids(tool_result: Any) -> set[str]:
    """Robustly parse stringified JSON tool results to find document IDs."""
    if isinstance(tool_result, str):
        try:
            parsed = json.loads(tool_result)
        except (json.JSONDecodeError, TypeError):
            return set()
    else:
        parsed = tool_result

    if not isinstance(parsed, list):
        return set()

    return {
        item.get("doc_id")
        for item in parsed
        if isinstance(item, dict) and item.get("doc_id")
    }