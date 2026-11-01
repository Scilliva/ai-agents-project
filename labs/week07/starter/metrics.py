"""Score retrieval by first relevant rank and section-level recall.

Read this before you write it, because the instrument matters more than the
number and the obvious instrument is the wrong one here.

**What this lab does NOT use, and why.** The obvious metrics are recall at
20 and precision at 5. On a corpus that chunks to about ninety-five pieces,
both are useless:

  recall at 20     twenty chunks is a fifth of the whole corpus, so it
                   saturates at 1.00 and stops distinguishing anything
  precision at 5   ten of the twelve questions have exactly one gold
                   section, so the highest it can score is one in five. It
                   returns exactly 0.20 on every question that works. It
                   is recall wearing a different name.

**What it uses instead.** The rank of the first gold chunk. It varies
continuously, it does not saturate, and it makes two retrievers comparable
on the same question. Recall at 5 sits beside it as the "did it work at all"
number.

The general lesson is worth more than the fix: a metric that cannot vary on
your data is not measuring your system. Check the range before you trust the
value, and week 10 makes the same argument about a judge.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Scored:
    qid: str
    rank: int | None            # rank of the first gold chunk, 1-based
    recall_at_k: float
    k: int
    retrieved: list[str]


def gold_keys(question) -> set[tuple[str, str]]:
    return {tuple(s.split("::", 1)) for s in question.gold_sections}


def rank_of_first_gold(ranked_chunks, question) -> int | None:
    """Where did the first correct chunk appear? 1-based.

    Return None when no gold chunk appears at all. That is a different
    failure from appearing at rank forty, and the two must not be averaged
    together.
    """
    wanted = gold_keys(question)
    if not wanted:
        return None
    for rank, chunk in enumerate(ranked_chunks, start=1):
        if chunk.key in wanted:
            return rank
    return None


def recall_at_k(ranked_chunks, question, k: int = 5) -> float:
    """What fraction of the gold SECTIONS made the top k?

    Compute it over sections, not chunks. A section split into three chunks
    that all appear should count once, or a question whose answer happens to
    be long scores higher for no reason.
    """
    sections = gold_keys(question)
    if not sections:
        return 0.0
    found = {chunk.key for chunk in ranked_chunks[:max(0, k)]}
    return len(sections & found) / len(sections)


def score(ranked_chunks, question, k: int = 5) -> Scored:
    return Scored(qid=question.qid,
                  rank=rank_of_first_gold(ranked_chunks, question),
                  recall_at_k=recall_at_k(ranked_chunks, question, k), k=k,
                  retrieved=[c.chunk_id for c in ranked_chunks[:k]])
