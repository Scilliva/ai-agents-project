"""Stage: memory, behind one `search` method. Replaced in weeks 6 and 7.

Week 6 replaces this file. Copy your `labs/week06/starter/memory.py` over
it; it has no sibling imports, so it needs no edit.

Week 7 replaces the BODY of `MemoryStore.search` and nothing else. The
signature stays exactly as it is below, which is why week 6 told you to keep
the matching inside that one method. Copy your `chunking.py`,
`corpus_loader.py`, and `retrieval.py` into `app/`, make their sibling
imports relative (`from chunking import` becomes `from .chunking import`),
copy the corpus to the root of your repository with
`cp -r labs/week07/corpus corpus`, and call your retriever from `search`.
If you never wired week 6, `search` still has its `@stub` line above it:
delete that line too, or the memory stage keeps reporting itself as a stub.

Keep these names and signatures, because `pipeline.py` calls them:

    MemoryStore.load(path) -> MemoryStore
    MemoryStore.search(subject, query, k=3) -> list[str]

The stub remembers nothing: `search` returns an empty list, which the
pipeline treats as "no memory and no retrieval", and `write` and `forget`
refuse. The handle methods below are week 6's, given complete.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field
from pathlib import Path

from .stub import stub

DEFAULT_PATH = Path("artifacts/memory_store.json")


@dataclass
class Fact:
    subject: str
    kind: str
    text: str
    handle: str
    written_at: str


@dataclass
class MemoryStore:
    path: Path = DEFAULT_PATH
    facts: list[Fact] = field(default_factory=list)
    cases: dict[str, str] = field(default_factory=dict)

    @stub(week=6, does="refuses: stores nothing")
    def write(self, subject: str, kind: str, text: str) -> str:
        raise NotImplementedError(
            "stub: memory is not wired in. Week 6 replaces app/memory.py.")

    @stub(week=6, does="remembers nothing: returns an empty list")
    def search(self, subject: str, query: str, k: int = 3) -> list[str]:
        return []

    @stub(week=6, does="refuses: there is nothing to forget")
    def forget(self, handle: str) -> bool:
        raise NotImplementedError(
            "stub: memory is not wired in. Week 6 replaces app/memory.py.")

    def open_case(self, subject: str) -> str:
        """Mint an explicit handle for a piece of ongoing state."""
        handle = f"case-{secrets.token_hex(6)}"
        self.cases[handle] = subject
        self.save()
        return handle

    def subject_of(self, handle: str) -> str | None:
        return self.cases.get(handle)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({
            "facts": [vars(f) for f in self.facts],
            "cases": self.cases,
        }, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = DEFAULT_PATH) -> "MemoryStore":
        store = cls(path=path)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            store.facts = [Fact(**f) for f in data.get("facts", [])]
            store.cases = data.get("cases", {})
        return store
