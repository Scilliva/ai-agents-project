"""The memory store, and the handle.

Two things live here and they are easy to confuse.

**Memory** is what the agent remembers about a resident across runs: facts,
written once and searched later. It is a store.

**A handle** is a name for a piece of state that the agent carries in its own
messages. It is not memory, it is an address. `open_case` mints one, and
every later call passes it back as an ordinary argument.

The distinction is the whole week. Block 2 shows why: when the protocol stops
carrying state for you, the state does not vanish, it becomes an argument
with a name the model can see.
"""

from __future__ import annotations

import json
import re
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path

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
    """A file-backed store. Deliberately not a database and not a vector store.

    Week 7 replaces `search` with real retrieval over embeddings. Keep the
    keyword version behind this one method and next week costs you ten lines
    instead of a refactor.
    """

    path: Path = DEFAULT_PATH
    facts: list[Fact] = field(default_factory=list)
    cases: dict[str, str] = field(default_factory=dict)

    # ----------------------------------------------------------------
    # Writing, and the handle it returns.
    # ----------------------------------------------------------------

    def write(self, subject: str, kind: str, text: str) -> str:
        """Append one fact and return a handle for it.

        Three decisions here, and all three go in DECISIONS.md with a reason.

        What does a handle look like? A sequential `fact-0007` tells anyone
        who sees it how many facts exist and lets them guess `fact-0006`,
        which is a read of somebody else's data. Week 12 attacks exactly
        this.

        What happens when a new fact contradicts an older one? Keeping both
        means `recall` can return two contradictory facts and something has
        to cope. Overwriting means losing what changed and when. Pick one.

        How long does a record live? Nothing here expires, which is a choice
        and the wrong one for a real service holding residents' data. If you
        keep it, say so rather than leaving it unsaid.
        """
        # Keep writes for auditability. Random handles avoid exposing record
        # counts or making adjacent records guessable. This lab store has no
        # expiry policy; the retention trade-off is recorded by the student.
        handle = f"fact-{secrets.token_urlsafe(18)}"
        self.facts.append(Fact(
            subject=subject, kind=kind, text=text, handle=handle,
            written_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
        self.save()
        return handle

    # ----------------------------------------------------------------
    # Searching, and what k costs.
    # ----------------------------------------------------------------

    def search(self, subject: str, query: str, k: int = 3) -> list[str]:
        """Return at most k remembered facts about ONE subject.

        Scope to the subject BEFORE you score anything. That is not an
        optimization, it is the boundary that stops one resident's memory
        leaking into another's conversation, and it belongs here rather than
        in a sentence asking the model not to do it.

        Keyword overlap is fine. Week 7 replaces the body of this method
        with embeddings and the signature does not change, so keep the
        matching inside this one method.

        Then answer, at the checkpoint: what does k cost you in tokens per
        call, and what happens when the store holds four hundred facts?
        """
        if k <= 0 or not query.strip():
            return []
        terms = set(re.findall(r"\w+", query.casefold()))
        # Enforce the privacy boundary before scoring relevance.
        scoped = [fact for fact in self.facts if fact.subject == subject]
        scored = []
        for index, fact in enumerate(scoped):
            words = set(re.findall(r"\w+", f"{fact.kind} {fact.text}".casefold()))
            overlap = len(terms & words)
            if overlap:
                scored.append((overlap, index, fact.text))
        scored.sort(key=lambda item: (-item[0], -item[1]))
        return [text for _, _, text in scored[:k]]

    # ----------------------------------------------------------------
    # Forgetting, which is not optional.
    # ----------------------------------------------------------------

    def forget(self, handle: str) -> bool:
        """Hard delete by handle. Return whether it existed.

        Not optional. A store that can only be written to is not a store you
        can operate, and "we keep everything forever" is an answer with a
        legal department attached to it.

        One line in DECISIONS.md about what this does NOT reach: anything
        already copied into a running conversation's messages. Deleting the
        fact does not un-say it.
        """
        old_size = len(self.facts)
        self.facts = [fact for fact in self.facts if fact.handle != handle]
        deleted = len(self.facts) < old_size
        if deleted:
            self.save()
        return deleted

    # ----------------------------------------------------------------
    # The handle, which is block 2's subject
    # ----------------------------------------------------------------

    def open_case(self, subject: str) -> str:
        """Mint an explicit handle for a piece of ongoing state."""
        handle = f"case-{secrets.token_hex(6)}"
        self.cases[handle] = subject
        self.save()
        return handle

    def subject_of(self, handle: str) -> str | None:
        return self.cases.get(handle)

    # ----------------------------------------------------------------
    # Persistence
    # ----------------------------------------------------------------

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
