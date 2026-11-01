# Week 7 practical: a RAG pipeline you can score

BPINFOR-132, Designing, Verifying, and Shipping AI Agents.
Duration: 2 teaching units, 90 minutes. Bring a laptop.

## What your system gains this week

Increment seven. Week 6 left your memory store searching by keyword, behind
one method, and told you to keep it there. Today that method's body is
replaced by embeddings and a vector store, and the signature does not change.

You also get the first honest measurement of retrieval quality, which is the
half of a RAG pipeline that can be scored without a single model call.

## Why this session exists

The lecture said that retrieval quality is measurable without generation,
and that measuring it separately is the only way to know which half of a RAG
pipeline failed. Blocks 1 and 2 are exactly that, and it is why today has no generation step at all.

## Learning outcomes exercised

Outcome 7 (an application integrating retrieval), outcome 8 (evaluation
design), outcome 12 (trade-offs).

## Before you arrive

Read the "RAG" section of AIE-Huyen chapter 6 and ADP-Gulli chapter 14.
Install the one new dependency:

```bash
pip install chromadb
```

## Timing

| Time | Block | What you do |
| 0 to 10 | Setup | Install, read the corpus and the twelve gold questions |
| 10 to 45 | Index and retrieve | TODO 1 to 3: chunk, embed, index, and two retrievers |
| 45 to 70 | Diagnose | TODO 4 and 5: read the table, and correct the gold set |
| 70 to 85 | Stretch | The compositional question, or a chunk sweep |
| 85 to 90 | Close | Commit, push, write the numbers into `DECISIONS.md` |

## The corpus and the gold set

Ten documents from a fictional Luxembourgish commune, chunking to about
ninety-five pieces. Twelve gold questions, each naming the **document and
section** that should be retrieved, never a chunk id. That is the design
decision to copy: the scorer resolves sections to chunk ids at scoring time,
so one gold set scores every chunking configuration you try.

The corpus is synthetic. Do not quote any fee or deadline in it as
information about Luxembourg.

## A warning about the instrument

The obvious metrics here are recall at 20 and precision at 5. Both are
useless on a corpus this size, and knowing why is worth more than the
metrics would be:

- **Recall at 20 saturates.** Twenty chunks is a fifth of the whole corpus.
  It scores 1.00 on ten of the eleven answerable questions.
- **Precision at 5 is pinned by an artifact.** Ten questions have exactly one gold section, so its ceiling is one in five. It returns exactly 0.20
  on every question that works. It is recall wearing a different name.

You will use the **rank of the first gold chunk** instead, with recall at 5
beside it. The general rule is the one to keep: a metric that cannot vary on
your data is not measuring your system, so check its range before you trust
its value. Week 10 makes the same argument about a judge.

## Block 1, index and retrieve (35 minutes)

TODO 1 in `chunking.py`, TODO 2 in `metrics.py`, TODO 3 in `retrieval.py`.

Do them in that order. A group that builds the index before the scorer works
ends up with a pile of retrieved passages and no way to say which are wrong,
which is the exact habit this session exists to break.

**Checkpoint 1.** The items in `checklist.md`.

## Block 2, diagnose (25 minutes)

TODO 4 and 5 in `01_retrieve.py`.

Ten of the eleven answerable questions will put the gold chunk at rank one.
Resist reporting that as success. It is evidence that the task is easy, and
the honest sentence says which.

**One question fails on both retrievers.** That is the centerpiece. Work out
why, and whether any chunk size would fix it.

**Then TODO 5, which is unusual.** One of the gold set's own notes claims
that a rare exact token is where dense retrieval loses and keyword search
wins. Your table will say the opposite. Rewrite the note to match your
evidence, in `goldset.py`, and record the correction.

That is not a trick. Course material is written by people who reasoned about
what should happen, and reasoning is what measurement is for checking. Your
own design notes are exactly as vulnerable.

**Checkpoint 2.** Be ready to name the failing question and say why.

## Wire it in

Retrieval goes behind your week 6 memory store's `search`, which is why
that brief told you to keep it behind one method. Copy `chunking.py`,
`corpus_loader.py`, and `retrieval.py` into `app/`, make their sibling
imports relative (`from .chunking import`, `from .corpus_loader import`),
and copy the corpus to the root of your repository with
`cp -r labs/week07/corpus corpus`. Then replace the body of
`MemoryStore.search(subject, query, k)` with the retriever and the chunk
size your `DECISIONS.md` chose, dense or keyword, without changing its
signature, and delete the `@stub` line above it if week 6 was never wired.
Prove it with `python -m app.run --subject "A. Muller" "How do I register a
new address?"`: the `memory.search` line should end in a hit count. If
you missed the session, keep the stub and record that in `DECISIONS.md`.

## What goes into DECISIONS.md today

Six entries. Template in `starter/DECISIONS_week07_section.md`.

1. Your chunker: size, overlap, and the one sentence behind those numbers.
2. The embedding model, its dimensionality, and the wall-clock time of one
   full indexing run.
3. The table: rank and recall at 5 per question, with the conditions.
4. Whether rank one on ten of eleven means your pipeline is good or the task
   is easy.
5. The question that fails on both, why, and whether chunk size fixes it.
6. The gold-set correction you made, and what it cost you to find it.

## Homework

- Run a chunk sweep at 300, 600, and 1200, and report which questions move.
  Report names, not means: the average will barely shift.
- Wire this retriever into your week 6 memory store's `search`, which is why
  the brief told you to keep it behind one method.
- `python -m project.verify` passing, gold set at 58 cases.

## If you finish early

- Fix the compositional question by asking two questions instead of one.
  Split it, retrieve for each, and merge. Report whether it works and what
  it costs.
- Take a question where keyword search ties dense retrieval and work out what
  is special about it. Then predict, before you run it, which other question would
  behave the same way.

## Reference solution

In `solution/`, published after the session. The written answer to TODO 5 is
at the bottom of `01_retrieve.py` and it is the part worth reading.
