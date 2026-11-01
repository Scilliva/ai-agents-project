"""The gold set: twelve questions, each with the sections that should be
retrieved.

Week 7, BPINFOR-132. Given to you complete. This is course data, not
starter code. Read it before you write anything, including the
ANNOTATION_NOTE.

Two design decisions in here are worth copying into your own project.

First, a gold passage is anchored to a document and a section heading,
never to a chunk id. Chunk ids change every time you change the chunker,
and a gold set that dies when you change the chunker cannot be used to
compare chunkers. Sections are resolved to chunk ids at scoring time.

Second, twelve questions that all succeed would be worthless. The value
of this set sits in the four awkward ones: one the corpus cannot answer,
one that needs two documents, one whose answer also appears in a
superseded document, and one that turns on a rare exact token.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from corpus_loader import Section, all_sections

ANNOTATION_NOTE = """
Convention used by this gold set, stated in advance so that a
disagreement is visible rather than silent:

1. Where a fee appears both on the service's own page and in the
   consolidated fee table on RB-TAXES, the gold passage is the service
   page. The fee table is treated as a near-duplicate, so retrieving it
   costs precision but does not count as a hit.
2. The superseded document RB-VIGNETTE-2024 is never a gold passage. It
   is in the corpus so that you can measure what your retriever does
   with out-of-date content.
3. A question that the corpus cannot answer has an empty gold list. It
   is scored on refusal, not on retrieval.

You may replace this convention. If you do, say so in DECISIONS.md and
re-score, rather than scoring against a convention you disagree with.
""".strip()


@dataclass(frozen=True)
class GoldQuestion:
    qid: str
    question: str
    gold_sections: tuple[str, ...]
    tags: tuple[str, ...] = field(default=())
    note: str = ""

    @property
    def answerable(self) -> bool:
        return bool(self.gold_sections)


GOLD: list[GoldQuestion] = [
    GoldQuestion(
        "Q01",
        "How much does a resident parking vignette cost per year?",
        ("RB-VIGNETTE::Fees",),
        ("distractor", "superseded"),
        "RB-VIGNETTE-2024 gives a different price and must not be retrieved "
        "above the current page. RB-TAXES mentions the vignette too.",
    ),
    GoldQuestion(
        "Q02",
        "I have been asked to fill in form RB-1140b. What is it for?",
        ("RB-VIGNETTE::How to apply",),
        ("rare-token",),
        "Although the query carries the rare exact string RB-1140b, the "
        "observed run ranks the gold section first with dense retrieval "
        "and fourth with keyword search, so both retrieve it in the top "
        "five and dense ranks it higher. This contradicts the claim that "
        "keyword search is the right tool; rankings can vary by run and "
        "configuration.",
    ),
    GoldQuestion(
        "Q03",
        "Within how many days of moving in must I declare my arrival?",
        ("RB-ARRIVEE::Deadline",),
        ("easy",),
    ),
    GoldQuestion(
        "Q04",
        "Which bin do grass and hedge cuttings go in, and when is it "
        "collected?",
        ("RB-DECHETS::Green waste",),
        ("vocabulary",),
        "The user says grass and hedge cuttings, the document says garden "
        "clippings. A vocabulary gap, which is where dense retrieval earns "
        "its price.",
    ),
    GoldQuestion(
        "Q05",
        "I have just moved to Remerbaach and I own a car. What do I have to "
        "do at the commune?",
        ("RB-ARRIVEE::Deadline", "RB-VIGNETTE::How to apply"),
        ("multi-document",),
        "No single section answers this. Retrieval has to bring back two "
        "documents, which is what makes recall at five interesting here.",
    ),
    GoldQuestion(
        "Q06",
        "Do I need to pay for the communal shuttle bus?",
        ("RB-TRANSPORT::Fares",),
        ("negation",),
        "The document says travel is free of charge. The question asks "
        "about paying, so the words barely overlap.",
    ),
    GoldQuestion(
        "Q07",
        "What proof of income does the childcare voucher application need?",
        ("RB-CSA::Documents required",),
        ("easy",),
    ),
    GoldQuestion(
        "Q08",
        "Do I need a building permit for a twelve square metre garden shed?",
        ("RB-BATIR::When a permit is required",),
        ("numeric",),
        "The threshold is ten square metres, so the answer requires a "
        "comparison the retriever cannot make. It only has to find the rule.",
    ),
    GoldQuestion(
        "Q09",
        "How much does a copy of a birth certificate cost?",
        ("RB-ETATCIVIL::Fees",),
        ("distractor",),
        "RB-TAXES::Fee table carries the same figure. See the annotation "
        "convention: the service page is the gold passage.",
    ),
    GoldQuestion(
        "Q10",
        "Who has to clear the snow on the pavement in front of a rented "
        "house?",
        ("RB-HIVER::Obligations of residents",),
        ("easy",),
    ),
    GoldQuestion(
        "Q11",
        "By when must I declare my dog to the commune?",
        ("RB-TAXES::Dog tax",),
        ("easy",),
    ),
    GoldQuestion(
        "Q12",
        "Is there free wifi in the communal park?",
        (),
        ("unanswerable",),
        "Nothing in the corpus answers this. A vector store still returns k "
        "results, so this question measures whether your pipeline can say "
        "that it does not know.",
    ),
]


def resolve(gold_sections, chunks) -> set[str]:
    """Turn section keys into the set of chunk ids that carry them.

    This is the function that makes the gold set survive a change of
    chunker. Call it after every re-chunking, never cache its output.
    """
    wanted = set(gold_sections)
    return {c.chunk_id for c in chunks if c.section_key in wanted}


def resolve_by_section(gold_sections, chunks) -> list[set[str]]:
    """One set of chunk ids per gold section, rather than one flat set.

    Needed because chunk-level recall is confounded by chunk size: halving
    the chunk size roughly doubles the number of chunks a gold section
    resolves to, so the same retriever appears to lose recall without
    having changed. Section-level recall asks the honest question instead,
    which is whether at least one chunk of each gold section came back.
    """
    return [{c.chunk_id for c in chunks if c.section_key == key}
            for key in gold_sections]


def gold_texts(gold_sections, sections: list[Section] | None = None
               ) -> list[str]:
    """The reference passages themselves, for RAGAS reference_contexts."""
    sections = sections if sections is not None else all_sections()
    by_key = {s.section_key: s.text for s in sections}
    return [by_key[key] for key in gold_sections if key in by_key]


def validate(sections: list[Section] | None = None) -> list[str]:
    """Every gold section must exist in the corpus. Run this after you
    edit either one."""
    sections = sections if sections is not None else all_sections()
    known = {s.section_key for s in sections}
    return [key for q in GOLD for key in q.gold_sections if key not in known]


if __name__ == "__main__":
    missing = validate()
    print(ANNOTATION_NOTE)
    print()
    print(f"{len(GOLD)} gold questions, "
          f"{sum(1 for q in GOLD if q.answerable)} answerable")
    for question in GOLD:
        tags = ",".join(question.tags) or "-"
        print(f"  {question.qid}  [{tags:<14}] "
              f"{len(question.gold_sections)} gold section(s)")
    print()
    print("missing gold sections:", missing or "none, the gold set is valid")
