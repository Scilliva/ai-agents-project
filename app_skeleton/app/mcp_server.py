"""Stage: the memory tools over MCP. Replaced in week 6.

The pipeline reads memory in process, through `memory.py`. This module is the
boundary for everything else: another process, another agent, or another
language that wants the same memory tools over HTTP.

Until you wire yours in, the tools are plain functions over the store and
serving refuses. To replace it, copy your `labs/week06/starter/mcp_server.py`
over this file and change its one sibling import:

    from memory import MemoryStore
    from .memory import MemoryStore

Then serve it from the root of your repository with
`python -m app.mcp_server`. It needs `pip install --pre "mcp==2.0.0rc1"`,
exactly as in week 6. Keep the five tool names, because a client that
learned them in week 6 calls them by name:

    remember(subject, kind, fact) -> str
    recall(subject, query, k=3) -> list[str]
    forget(handle) -> bool
    open_case(subject) -> str
    case_subject(handle) -> str
"""

from __future__ import annotations

from .memory import MemoryStore
from .stub import stub


@stub(week=6, does="refuses: memory is a stub")
def remember(subject: str, kind: str, fact: str) -> str:
    return MemoryStore.load().write(subject, kind, fact)


@stub(week=6, does="pass-through to the stub store: returns nothing")
def recall(subject: str, query: str, k: int = 3) -> list[str]:
    return MemoryStore.load().search(subject, query, k)


@stub(week=6, does="refuses: memory is a stub")
def forget(handle: str) -> bool:
    return MemoryStore.load().forget(handle)


@stub(week=6, does="pass-through to the store")
def open_case(subject: str) -> str:
    return MemoryStore.load().open_case(subject)


@stub(week=6, does="pass-through to the store")
def case_subject(handle: str) -> str:
    return MemoryStore.load().subject_of(handle) or ""


if __name__ == "__main__":
    raise SystemExit(
        "app/mcp_server.py is still the stub, so there is no server to run.\n"
        "Week 6 replaces it: copy labs/week06/starter/mcp_server.py over it\n"
        "and change `from memory import` to `from .memory import`.")
