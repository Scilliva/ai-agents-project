# Week 2 practical: a structured-output extractor, measured

BPINFOR-132, Designing, Verifying, and Shipping AI Agents.
Duration: 2 teaching units, 90 minutes. Bring a laptop.

## What your system gains this week

Increment two. Week 1 gave you a repository, one working call, and a
measured claim about when the model repeats itself. Today the call becomes a
component with a contract: an extractor that turns a free-text message into
a validated record, plus the scorer that says whether it worked.

You also write the first ten cases of the gold set that weeks 3, 7, and 10
all build on. That file is the single most valuable thing you produce today,
and it is the one nobody feels like writing.

## Why this session exists

The lecture argued that a prompt is a versioned artifact with a
specification inside it, and that no prompt change counts as an improvement
until it has been measured on data it was not written against. This session
is that claim put to work, twice.

You will produce a number that settles a design argument. Today it is on ten
records, which is far too few to be confident about anything, and part of
the exercise is being able to say so out loud while still using the number.

## Learning outcomes exercised

Outcome 1 (building blocks), outcome 6 (decomposing a problem into a
system), and outcome 12 (justifying trade-offs). The gold set feeds outcome
8, which is examined in week 10.

## Before you arrive

Read AIE-Huyen chapter 5, in particular the sections on clear and explicit
instructions and on in-context learning. Skim ADP-Gulli Appendix A.

Have week 1 committed, and run `python 00_preflight.py` from the week 1 lab
once so your model is loaded. The first schema-constrained call after a cold
start takes several minutes while the grammar compiles. Every call after
that takes about four seconds. Do not discover this at minute three.

## Timing

| Time | Block | What you do |
| 0 to 12 | Setup | Read the corpus, agree what a correct extraction is, warm the model |
| 12 to 45 | Zero-shot | TODO 1 to 4 and 7: schema, prompt, scorer, gold set |
| 45 to 70 | Few-shot | TODO 5 and 6: examples chosen deliberately, then the same scorer |
| 70 to 85 | Sensitivity | TODO 8: one variant per group, measured |
| 85 to 90 | Close | Commit, push, write the numbers into `DECISIONS.md` |

## The task, and why it is shaped this way

Ten short messages to the help desk of Remerbaach, a fictional Luxembourg
commune, in English, French, and German. Four fields out of each.

Every field is there to exercise something specific.

- **category** and **urgency** are closed label sets, so a wrong answer is
  detectable with no model and no judgment.
- **due_date** is nullable, so the absent case has to be specified rather
  than discovered. This is where the model fails most, and it fails by
  inventing a plausible date rather than by refusing.
- **quote** must appear verbatim in the source, so one field is checkable
  by string search, for free. It is the only free check you get this
  semester and it is worth understanding why it works.

Ten records is small and you should say so at the checkpoint. It is enough
to see a difference and nowhere near enough to be confident about one.

## Working with the recording

Every model answer for every variant is recorded in `fixtures/replay.json`,
sixty calls in all.

```bash
python starter/01_zero_shot.py --replay      # instant, no model
```

Write your scorer against the recording. It runs in well under a second, so
you can iterate properly instead of waiting forty-five seconds to discover
you compared the wrong field. Then run it live and confirm your machine
agrees.

The recording contains real failures, unedited. **If your scorer reports
forty out of forty, your scorer does nothing.** The reference run scores
36 of 40, and the four failures are the interesting part of the session.

## Block 2, the zero-shot baseline (33 minutes)

TODO 1 and 2 in `extractor.py`, TODO 3 and 4 in `scoring.py`, TODO 7 in
`01_zero_shot.py`.

The order matters. Write the scorer before you tune the prompt, because a
scorer written after you have seen the output tends to score what the output
already does.

**Checkpoint 1.** The six items in `checklist.md`.

## Block 3, the few-shot variant (25 minutes)

TODO 5 and 6 in `02_few_shot.py`.

Same schema, same scorer, same ten documents. One variable changes. Two ways
to break that, both easy:

- editing the schema or the scorer between runs, which makes the numbers
  incomparable
- taking examples from `DOCS` rather than from `EXAMPLE_POOL`, which turns
  the second measurement into a memory test

Report per field, never as one number. In a well designed comparison some
fields move and some do not, and being able to say which is the whole skill.

**Checkpoint 2.** Be ready to read your table out loud, per field, as
counts.

## Block 4, sensitivity (15 minutes)

TODO 8 in `03_sensitivity.py`. Your instructor assigns you one variant, so
that the plenary has four results instead of one.

The point is not which variant wins. It is that a change nobody would flag
in a code review moves a measured number.

## What goes into DECISIONS.md today

Six entries. Template in `DECISIONS_week02_section.md`.

1. Your output contract: the null convention, the date format, and why.
2. The zero-shot table, per field, as counts.
3. The few-shot table, the examples you chose, and one line per example
   saying which field it was meant to move.
4. What got worse, if anything, and your diagnosis.
5. The token cost of the example block, per call and per thousand calls.
6. Which variant you would ship, on what evidence, and what would change
   your mind.

## Homework

- Run both variants live if you only ran the recording in the session, and
  note any disagreement with the reference numbers.
- Finish the gold set if you did not: ten cases, each with an
  `expected_behavior` sentence a colleague could grade against. Week 10
  reloads this file.
- Run `python -m project.verify` and commit with it passing.

## If you finish early

- Run the whole comparison on `qwen2.5:7b`. Predict first: which of the four
  fields does a larger model help most? The answer is not obvious, and the
  field that is pure convention may not be the one that moves.
- Take the three documents where the zero-shot run invented a due date. Can
  you fix all three with one sentence added to the prompt, without breaking
  the two that correctly extract a date? That tension is the exercise.
- Add an eleventh document of your own, written to break your extractor, and
  add it to the gold set with its expected behavior. Adversarial cases you
  wrote yourself are worth more in week 12 than any you were given.

## Reference solution

In `solution/`, published after the session. The written answer to TODO 6 is
at the bottom of `solution/02_few_shot.py` and it is the part worth reading.
