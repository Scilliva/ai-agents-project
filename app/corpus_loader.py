"""Reading the corpus. Given complete.

Ten documents from a fictional Luxembourgish commune, written for this
course. Front matter carries a doc_id and a title, and `## ` headings mark
sections. The gold set anchors to (doc_id, section), never to a chunk id,
which is what lets one gold set score every chunking configuration you try.

The corpus is synthetic. Do not quote any fee, deadline, or procedure in it
as information about Luxembourg.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

CORPUS = Path(__file__).resolve().parent.parent / "corpus"


@dataclass(frozen=True)
class Section:
    doc_id: str
    title: str
    section: str
    text: str

    @property
    def key(self) -> tuple[str, str]:
        return (self.doc_id, self.section)

    @property
    def section_key(self) -> str:
        """The form the gold set names sections in: DOC-ID::Section."""
        return f"{self.doc_id}::{self.section}"


def load_sections(corpus: Path = CORPUS) -> list[Section]:
    """Every document split at its `## ` headings."""
    out: list[Section] = []
    for path in sorted(corpus.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        meta: dict[str, str] = {}
        if raw.startswith("---"):
            head, _, raw = raw.partition("---\n")[2].partition("---\n")
            for line in head.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    meta[k.strip()] = v.strip()
        doc_id = meta.get("doc_id", path.stem)
        title = meta.get("title", path.stem)

        section, buf = "(intro)", []
        for line in raw.splitlines():
            if line.startswith("## "):
                if "".join(buf).strip():
                    out.append(Section(doc_id, title, section,
                                       "\n".join(buf).strip()))
                section, buf = line[3:].strip(), []
            else:
                buf.append(line)
        if "".join(buf).strip():
            out.append(Section(doc_id, title, section,
                               "\n".join(buf).strip()))
    return out


# The gold set validator calls this name. Kept as an alias so that
# goldset.py needs no edit: one loader, two names, and the older one is the
# one the gold set was written against.
all_sections = load_sections
