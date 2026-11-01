# Chunking strategy comparison worksheet

BPINFOR-132, week 7. One page. Keep it open during block 1 and finish it
during block 3 if you run the chunk sweep.

Chunking is the design decision with the longest half-life in a RAG
pipeline. It is made once, offline, before anything else exists, and every
number you measure afterwards is conditioned on it. This worksheet exists so
that you make it deliberately rather than by accepting a default.

The working definition to hold onto: **a chunk should be the smallest piece
of text that can answer a question on its own.**

## Part 1, the four strategies

| Strategy | How it cuts | Strong when | Fails when |
| Fixed size | Every N characters or tokens, with an overlap | The corpus is uniform prose and you need something working today | The corpus has tables, lists, or short sections. It cuts through structure without noticing. |
| Recursive | Paragraphs, then sentences, then characters, until the piece fits | Almost always. This is the default and the one to beat. | A single paragraph is longer than the target size, so it degrades to a hard cut anyway |
| Structure-aware | On the document's own headings, list items, or table rows | The corpus has real structure and one parser covers most of it | Documents with no structure, or a format you have no parser for |
| Semantic | Where consecutive sentences stop being similar | Long unstructured narrative with real topic shifts | Anywhere. It costs embedding calls at ingestion and a bad cut is hard to explain. |

## Part 2, the five knobs, and the failure at each extreme

| Knob | Too small | Too large | Your value | Why |
| Chunk size | The answer is split across chunks, so no chunk answers alone | The passage is mostly irrelevant text, so precision collapses | | |
| Overlap | Facts on a boundary are lost from both neighbours | Near-duplicate passages occupy two of your five slots, and you paid to embed them twice | | |
| Boundary rule | Sentences and table rows cut mid-structure | Whole documents as chunks, so ranking has nothing to rank | | |
| Metadata kept | No source and no section, so no citation can be checked | Metadata longer than the text, and filters nobody uses | | |
| Unit indexed | Sentences: precise to find, useless to read | Sections: easy to read, hard to rank | | |

There is no globally correct setting. The right chunk size for dense legal
clauses is not the right one for short help pages. The only way to know is to
measure retrieval on your own gold set.

## Part 3, run the sweep and fill this in

`python 05_stretch.py sweep` builds three indexes over the same corpus and
scores the same gold set against each. Fill in what you observe.

| Size / overlap | Chunks | Index cost (EUR) | Recall @20 | Section recall @20 | Precision @5 | MRR |
| 300 / 40 | | | | | | |
| 600 / 80 | | | | | | |
| 1200 / 120 | | | | | | |

Two recalls, on purpose. Plain chunk-level recall is confounded by the very
thing you are comparing: halving the chunk size roughly doubles the number of
chunks a gold section resolves to, so the denominator grows while the
retriever has not changed. Section-level recall asks instead whether at least
one chunk of each gold section came back, and it is the honest number here.
Choosing a metric that moves for a mechanical reason is a real and common
evaluation mistake, and this is the cheapest place in the course to meet it.

Then answer these five questions in `DECISIONS.md`. They are worth more than
the table.

1. Which direction did recall move as chunks got larger, and why? State the
   mechanism, not the observation.
2. Which direction did precision move, and why? The mechanism is different
   from the one in question 1.
3. By how much did the two recalls disagree, and which one would you put in a
   report? Say why.
4. Which questions changed rank between the smallest and largest setting?
   Name them. A question that moved is more informative than an average that
   did not.
5. Which configuration would you ship, and what would change your mind? A
   defensible answer names a cost or a latency number, not a preference.

## Part 4, the trick that usually beats all three

Parent and child chunks. Index the small chunks, because retrieval is a
ranking problem and small units rank precisely. Then hand the generator the
enclosing section, because generation is a reading problem and larger units
read better. You retrieve on one unit and generate on another, deliberately.

About ten lines of code. It resolves the tension in Part 2 rather than
trading one side of it against the other, and it is the first thing to try in
your project once the sweep tells you that neither extreme is comfortable.

## Part 5, the things people forget

- The chunk should carry its own heading in its text. Two lines of code, and
  it measurably helps both dense and keyword retrieval, because a chunk that
  says only "60 euros per year" is unfindable.
- Chunk ids should be derived from the document and the offset, never from a
  running counter, or you cannot update one document without rebuilding
  everything.
- Changing the chunker means re-indexing, and re-indexing costs the full
  embedding bill again. Budget for three runs, not thirty.
- Your gold set must be anchored to documents and sections, or changing the
  chunker destroys it and this whole worksheet becomes impossible.
