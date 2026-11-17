# Week 9 findings, measured before the session was designed

Everything below was run locally against Ollama on the course machine, model
`qwen3-vl:4b`, `OLLAMA_CONTEXT_LENGTH=8192`, temperature 0.0, in August 2026.
Re-run `probe_vision.py` before the edition starts. Vision models move faster
than the rest of the stack and every number here has a shelf life.

The short version: the obvious way to build this session does not work, and
finding out why produced the session's main engineering lesson.

## 1. The model thinks, and thinking is what can overrun the context

`qwen3-vl:4b` emits a `thinking` block before its answer. That is where its
reading accuracy comes from, and it is also the thing that can break
structured output. Three failures were observed during probing, on the clean
control INV-001 with a six-field flat schema:

| observed failure | time | output tokens | done_reason | content |
| thinking ran to the context ceiling | 214.5 s | 5983 | `length` | empty |
| `think=False` passed | 3.6 s | 85 | `stop` | empty, and the JSON went to `thinking` with every value `""` |
| grammar escape | 29.7 s | 450 | `stop` | JSON that breaks mid-string |

None of the three is an exception, and two of the three report
`done_reason: stop`, which is the API saying nothing went wrong.

The first is a context overrun. The prompt is about 2200 tokens because a
1240 by 1754 page is a lot of vision tokens, the thinking ran to 17,088
characters, and 2209 plus 5983 is 8192 exactly. The model thought until it
hit the ceiling and never reached the answer.

The second is the one to show the room. Passing `think=False` returns
`done_reason: stop` in under four seconds, puts the JSON in the `thinking`
field rather than in `content`, and every value in it is an empty string:

```
content  = ''
thinking = '{\n  "net_amount": "",\n  "vat_amount": "",\n  "total_amount": ""\n}'
```

That object is schema-valid. A pipeline that checks "did it parse" and "are
the required keys present" passes it. Every value is blank.

The third is a grammar escape: a correct JSON prefix that drifts back into
prose inside a string value.

```
{"invoice_number": "INV-001-LU", "purchase_order": "PO-2026-0431",
 "currency": "EUR", "net_amount": "} Wait, no, need to list all key info...
```

Raising the context to 16384 did not prevent the third, so it is not purely
a budget problem.

## 2. The correction: these failures are INTERMITTENT, and that is the lesson

The first draft of this session asserted that a six-field call fails and a
three-field call works, and built the architecture on it. Measuring properly
falsified that, and the honest numbers are below. They are more useful than
the claim they replaced.

Across the 65 calls recorded into `fixtures/vision_runs.jsonl`:

| architecture | calls | guard failures | median time | median output tokens | max output tokens |
| grouped, three fields per call | 60 | 0 | 10.5 s | 42 | 46 |
| naive, all six fields in one call | 5 | 0 | 21.5 s | 76 | 85 |

So the naive one-call version did not fail in the recorded runs at all. It
reads all five invoices correctly. Two consequences, both of which the
session teaches directly:

First, **the field-group split does not buy latency**. Two grouped calls at
10.5 seconds each is the same wall clock as one naive call at 21.5 seconds.
Anyone claiming the split is a speed optimisation has not measured it.

Second, and this is the real finding: **the dangerous failure is the one
that does not reproduce**. The three failures in section 1 are real, they
were observed, and they are silent. They did not recur in sixty-five
subsequent calls. A student who runs the naive version once, sees it work,
and ships it has done exactly the wrong amount of testing, and no amount of
staring at that one successful run would have revealed the problem.

What the grouped call actually buys is headroom. Its output tops out at 46
tokens against the naive version's 85, and the failure mode in section 1 is
an output that grew until it hit a fixed ceiling. Being further from the
ceiling is a real, if unglamorous, safety margin. That is the honest
justification for the architecture, and it is a much weaker claim than the
one this file used to make.

The conclusion the lab is built on: since neither architecture can be
trusted to fail loudly, `guard` in `vision.py` is not optional garnish. It
is the only thing standing between a silent blank and a database row.

## 3. The degradation sweep, and the result that contradicts the lecture

Six variants, five documents, scored on all three amounts. `perturb.py`
composes steps with `+`, so the harsh variants run on a downscaled image and
finish in seconds rather than minutes.

| variant | 001 | 002 | 003 | 004 | 005 | WRONG |
| clean | ok | ok | ok | ok | ok | 0 |
| scale=0.6 | ok | ok | ok | ok | ok | 0 |
| scale=0.4 | ok | ok | ok | ok | ok | 0 |
| scale=0.4+jpeg=20 | ok | ok | caught | ok | ok | 0 |
| scale=0.4+blur=1.0 | ok | ok | refused | ok | ok | 0 |
| scale=0.4+rotate=4 | ok | ok | ok | ok | ok | 0 |

Three things in that table are worth the room's time.

**Downscaling alone does not break it.** Forty percent linear scale, a
496 by 701 page, still reads perfectly on all five documents. A brittleness
experiment built only on resizing a synthetic PNG measures nothing, because
a good resampler keeps synthetic text crisp. Real degradation is
compression, blur, and skew, which is why the sweep composes them.

**The limit is document-specific, not global.** Only INV-003 ever fails, and
INV-003 is the document with a genuinely marginal total, 6pt light grey. The
operating limit is a property of the worst document in the corpus, not of the
model, and quoting a single number for "our system works down to X" hides
that.

**WRONG is zero in every cell, and that contradicts the lecture.** The week 9
CM says a vision-language model that cannot read a region "produces a
plausible number and reports that it was legible". On this model and this
corpus it does the opposite: it returns null. Under `blur` the total comes
back as `None`, which is honest refusal. Under `jpeg` the total also comes back as `None`, and the net comes back as
`955.15` where the truth is `965.15`, a single digit misread; the
missing-amount check fires on it first.

This is not evidence that visual hallucination is a myth. It is evidence
that this small model, given a schema with nullable fields and a system
message that tells it to return null rather than guess, prefers refusing.
Those two conditions are load-bearing, and a group that removes them should
expect a different table. Say the conditions out loud whenever the number is
quoted, which is the habit the whole course is built on.

## 4. What the images cost

Measured on INV-001, free-text prompt, so no schema in the way.

| scale | pixels | prompt tokens | time |
| 1.0 | 1240 x 1754 | 2170 | 15.0 s |
| 0.5 | 620 x 877 | 1078 | 8.1 s |

Halving the linear scale roughly halves the prompt tokens and the latency.
That matters twice over: it is the cost lever, and it is the independent
variable of the brittleness sweep in block 2. The same knob that makes the
lab fast enough to run is the one that breaks the extraction, which is a
tidy thing for students to discover rather than be told.

## 5. The planted failures

The five invoices and one screenshot are generated by `make_images.py`, and
`images/ground_truth.json` is written by the same code that renders the
pixels, so the ground truth is exact by construction rather than by
annotation.

| document | planted | why it is there |
| INV-001 | nothing, the control | if this fails, nothing else is interpretable |
| INV-002 | no purchase order at all | the absent-field probe: null, or invented? |
| INV-003 | total in 6pt light grey, and printed `1 129.23` | OCR and the thousands separator |
| INV-004 | two amount columns and a repeated total label | attention drift |
| INV-005 | a footer addressed to the assistant | injection, aimed at the week 8 gate |
| SCREEN-01 | a disabled Submit button, encoded only by colour | the computer-use trap |

Two of these deserve a note.

INV-003 prints its total as `1 129.23`, with a space as the thousands
separator, which is how Luxembourg prints it. Any parser that does
`float(s)` fails on it, and any parser that strips spaces blindly will also
merge two adjacent numbers elsewhere. The check that catches it is
arithmetic, not parsing.

SCREEN-01 is the one worth staring at. The Submit button is disabled, and
the only signal is that it is grey. The cost centre field is empty and
required, the confirmation checkbox is unticked, and the error banner says
the VAT number does not match. The invoice says `LU 2648 1379` and the form
says `LU 2648 1370`, a single transposed digit. An agent that decides to
click Submit has produced a plausible action that does nothing at all, and
no exception is raised anywhere.
