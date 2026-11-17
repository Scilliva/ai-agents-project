# Week 10 practical: an evaluation you can trust

BPINFOR-132, Designing, Verifying, and Shipping AI Agents.
Duration: 2 teaching units, 90 minutes. Bring a laptop and your project
repository, with every artifact your earlier sessions wrote.

## Where this fits

Nine weeks of building stop today. From here the course asks whether any of
it works, and this is the first session that consumes rather than produces.

You will not write a new agent. You will read back the traces your own
sessions recorded since week 3, through the same `Trace` contract they were
written with, and turn them into numbers that can fail a build.

The order of the session is its argument, so it is worth stating plainly.
Block 1 measures everything that costs zero model calls, and it is the
larger block on purpose. Block 2 adds a judge, and spends most of its time
deciding whether you are allowed to trust it. Block 3 turns both into gates.

## Why this session exists

Because the number everyone reports is the one that hides the most.

Run block 1 and you will get a table of five numbers per week. Week 9 has the
best accuracy in it, 1.00, and no evidence at all on three of the four
reliability dimensions, because nothing ever failed, so there was nothing to
be reliable about. Week 8 has the worst accuracy, 0.25, and by a distance the
best predictability, 0.83, because its failures were injected on purpose and
its code says so when they happen.

Rank those three systems by accuracy and you get them in close to the reverse
of the order you would trust them in. That is the AAR-Rabanser finding
reproduced on your own project's logs rather than quoted from a paper, and it
is why the reliability block exists.

## Learning outcomes exercised

Outcome 7 (designing and implementing an evaluation harness for a
foundation-model system, including deterministic checks, model-graded
metrics, and their validation), outcome 8 (interpreting evaluation results
and distinguishing benchmark performance from operational reliability),
outcome 12 (justifying trade-offs in cost, latency, reliability, and safety),
and outcome 2 (the reliability dimensions and why a single success rate is
not enough). This is the tenth increment of the project deliverable.

## Before you arrive

Read AIE-Huyen chapters 3 and 4, and the four-dimension frame in
AAR-Rabanser. Then check that your project actually has something to
evaluate:

```bash
python -c "import json,pathlib; print(len(pathlib.Path('artifacts/traces.jsonl').read_text().splitlines()), 'traces')"
```

If that prints zero, your own system has nothing to evaluate yet, so come
to the lab early. The starter ships the course's own 62 traces, from weeks
5, 8, and 9, as `fixtures/reference_traces.jsonl`. When your
`artifacts/traces.jsonl` is missing or empty, the harness reads those
instead and says so: `01_free.py` prints a note, and `pytest` names the
reference at the end of its run. You can do the whole session against them,
but an evaluation of the reference is a measurement of the reference, and
the point of the session is to read your own.

Then run your application over your gold set, twice, with nobody present.
This is the run your harness evaluates as the system you submit, and twice
is what gives consistency something to measure:

```bash
python -m app.run --batch --repeat 2
```

On a local model this takes a few minutes per pass, so do it at home rather
than in block 1. Install the harness:

```bash
pip install -r starter/requirements.txt
```

## Timing

| Time | Block | What you do |
| 0 to 8 | Set up | Install, count your traces, read the free layer idea |
| 8 to 40 | The free layer | TODO 1 and 2, then `01_free.py` |
| 40 to 45 | Start the judge | `python 02_judge.py` live, then keep working |
| 45 to 70 | The judge | TODO 3 and 4, the labels, and the threshold sweep |
| 70 to 85 | The gates | TODO 5, then `pytest` |
| 85 to 90 | Close | Commit, push, and write `DECISIONS.md` |

The judge run is about fifty seconds for twelve cases, so it is short. Start
it anyway at the top of the block: it writes each judgment to the fixture as
it arrives, so an interrupted run costs you one call rather than all twelve.
`02_judge.py --replay` reads the recorded judgments instantly.

## What you build

| File | Marker | What it is |
| `dimensions.py` | TODO 1a, 1b | consistency and robustness, from traces |
| `dimensions.py` | TODO 2a, 2b | predictability and safety |
| `judge.py` | TODO 3a, 3b | a GEval judge against the local model |
| `judge.py` | TODO 4 | validation against hand labels |
| `test_harness.py` | TODO 5a, 5b, 5c | three gates that can fail a build |

TODO 4 is the one with the trap in it, and it is worth reading twice before
you start.

## The three things this session insists on

**A dimension with no evidence is `None`, not zero.** If no case was ever run
twice under identical conditions, your consistency is unknown, and reporting
it as 0.00 is a lie in the other direction. Block 1 will hand you several
`n/a` cells. Two of them are defects rather than absences: look at the case
ids in weeks 5 and 8 and say what went wrong when they were named.

**Label before you judge.** Twelve cases are labelled by hand in `judge.py`,
four obvious and eight genuinely arguable, and they were written before any
judge ran. A label written after seeing the score is not a label. Disagree
with the ones you disagree with, in writing, and say why.

**A judge is a model AND a threshold.** On the reference data the judge
agrees with all twelve labels, which sounds like a finished instrument until
you sweep the threshold: perfect agreement holds only between 0.45 and 0.55.
Nobody chose 0.5, it is the library default, and on this data it happens to
land in the middle of the only band that works. Below it you get false
passes, which means a green gate on an invented answer. Above it you get
false fails, which cost a human's attention and nothing worse. The two are
not symmetric, and if you must be wrong, be wrong on the high side.

## What to expect, so you do not misread it

Your judge will probably agree with most of the labels. That is not a
finished validation, it is a starting point, and the threshold sweep is what
turns it into evidence. A group that reports "our judge agrees 12 out of 12"
without the sweep has reported the least interesting true thing available.

Expect block 1 to produce numbers that look bad. Low accuracy on week 8 is
correct: those runs had faults injected on purpose. This is the session where
you learn that a number is not comparable across systems without its
conditions, so write the conditions down.

## The stretch, if you finish early

`ragas_metrics.py` runs RAGAS faithfulness against the passages your week 7
retriever actually returned. It asks a different question from today's
judge, and the difference is worth understanding: the judge compares an
answer to a REFERENCE answer, while faithfulness compares it to the
retrieved context. That separates "the generator invented something" from
"the retriever fetched the wrong passage", which are different bugs with
different fixes and which a single score cannot tell apart.

It is deliberately outside the ninety minutes. Run it, and add one line to
DECISIONS.md saying which of your own failures each metric would catch.

## Where the harness reads from

Everything here reads `artifacts/traces.jsonl`, the file every session and
your application have appended to. Your application marks its runs with
`notes["source"] = "app"`, so `01_free.py` prints them as their own `app`
row, and the gate on condition keys checks each week per writer rather than
mixing your application with a lab script run the same week. That `app` row
is the system you submit, and it only exists if you ran
`python -m app.run --batch --repeat 2` before the session. The traces of
every stage still marked as a stub say so in `notes["stubbed"]`, and an
evaluation of a stub is a measurement of the stub.

## Homework

Add your week 9 cases to the gold set, which currently stops at week 7, and
say in one line what each new case is for. A gold set that stopped growing is
a gold set that stopped being used.

Then run `pytest -m "not judged"` in whatever passes for your CI, or in a
git pre-commit hook, and record what it costs in seconds. The free gates are
the ones you can afford to run on every commit, and knowing their cost is
what makes that claim more than an intention.
