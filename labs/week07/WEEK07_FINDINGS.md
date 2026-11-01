# Week 7: the instrument is wrong, and one gold-set claim is false

Written 2026-08-10, during the practical-track redesign. Week 7 was probed
before being rebuilt. The corpus and the gold set are good. The
**measurements** the session asks for are the wrong instrument for this
corpus, and one of the gold set's teaching claims is contradicted by the
data.

Reproduce with the probe kept in the session scratch directory. Measured on
`nomic-embed-text` at 768 dimensions, 95 chunks from 10 documents, chunked
at 600 characters with 80 overlap.

## What is good and should be kept

The corpus and the gold set are well built. Twelve questions, anchored to a
document and a section rather than to chunk ids, so the same gold set scores
any chunking configuration. Tags for distractor, superseded, rare token,
vocabulary gap, multi document, negation, and one unanswerable question.
That design is right and none of it needs changing.

Embedding the whole corpus takes under two seconds, so the session is not
waiting on anything.

## Defect 1: recall at 20 and precision at 5 measure nothing here

The brief and the deck ask for recall at 20 and precision at 5. On a
95-chunk corpus:

- **Recall at 20 saturates.** Twenty chunks is a fifth of the entire
  corpus. Measured: 1.00 on ten of the eleven answerable questions.
- **Precision at 5 is pinned by an artifact.** Ten of the twelve questions have exactly one gold section, so the highest precision at 5 they can
  score is one in five. Measured: exactly 0.20 on every question that
  succeeded, and 0.00 on the one that failed. It is recall wearing a
  different name.

So the two headline numbers of the session are a constant and a saturated
one. Students would spend the block computing them correctly and learn
nothing from either.

**What to use instead.** The rank of the first gold chunk. It varies
continuously, it does not saturate, and it makes the dense against keyword
comparison legible. Recall at 5 is worth keeping alongside it as the
"did it work at all" number.

## Defect 2: the rare-token claim is false on this embedder

Q02 asks about form `RB-1140b`, and the gold set says:

> Rare, exact, and semantically empty, so dense retrieval is the wrong tool
> for it and keyword search is the right one.

Measured rank of the first gold chunk:

| question | tag | dense | keyword |
| Q01 | distractor, superseded | 1 | 2 |
| **Q02** | **rare-token** | **1** | **12** |
| Q03 | easy | 1 | 3 |
| Q04 | vocabulary | 1 | 1 |
| Q05 | multi-document | 22 | 30 |
| Q06 | negation | 1 | 7 |
| Q08 | numeric | 1 | 1 |
| Q11 | easy | 1 | 5 |

Dense retrieval ranks it **first**. Keyword search ranks it **twelfth**, and
the reason is visible in the corpus: the superseded 2024 page carries the
near-identical string `RB-1140a`, and the current page carries `RB-1140b` in the gold section and again under
"Visitors", so a term-overlap scorer spreads its score across the wrong chunks.

This matters beyond one row. The hybrid-retrieval stretch is built on the
premise that keyword search rescues the rare-token question. It does not.
On this corpus, with this embedder, dense wins everywhere or ties.

Three ways forward, and the choice is a teaching decision:

1. **Report it as the finding.** Keep the question, keep the tag, and let
   students discover that a claim in their own gold set does not survive
   measurement. That is honest and it is the course's own discipline applied
   to the course's own material.
2. **Find a rare token that does defeat dense retrieval.** It probably
   exists, and finding it is a probe rather than a guess.
3. **Change the corpus** so the rare token appears once, in the gold
   section only. That makes keyword search win and makes the lesson land as
   originally intended, at the cost of being arranged.

Option 1 is the cheapest and the most in keeping with the rest of the
course. Option 2 is the most useful if a token can be found.

## The one genuinely hard question, and it should be the centerpiece

Q05, "I have just moved to Remerbaach and I own a car. What do I have to do
at the commune?", needs two documents together. It is the only question that
fails, and it fails on both retrievers: rank 22 dense, rank 30 keyword.

That is the finding the session should be built around. It is a real
limitation of single-vector retrieval on a compositional question, students
can see exactly why, and it motivates everything from query decomposition to
the reranking conversation in weeks 10 and 11.

## What has not been decided

The vector store. `CLAUDE.md` left Chroma or LanceDB open when this was written; Chroma has since been settled. The probe used
about twenty lines of cosine similarity, which is enough for 95 chunks and
adds no dependency. Using a real store is still the right call for the
syllabus, which introduces it as a black box, but it is worth confirming the
install is quick before committing a session to it.

Nothing has been built for week 7. The corpus, the gold set, and the twelve
questions are unchanged and are worth keeping.
