# Week 2 checklist

## Checkpoint 1, the zero-shot baseline

Six items. Do not move to block 3 until all six are true.

- [ ] Ten documents extracted and validated, with no unhandled validation
      error, and the invalid count reported even if it is zero
- [ ] Per-field counts computed separately for category, urgency, due_date,
      and quote. Not one overall accuracy.
- [ ] The quote field checked by substring search against the source, not by
      eye and not with any normalization
- [ ] Your scorer counts a record that failed validation as wrong on every
      field, rather than skipping it
- [ ] Input and output tokens recorded, and the cost per thousand calls
      estimated
- [ ] One sentence written down predicting whether examples will help, and
      on which field. Write it before you run block 3.

**If your scorer reports 40 out of 40 on the recording**, it does nothing.
The reference run scores 36 of 40. Find the four.

## Checkpoint 2, does showing beat telling

Six items. Be ready to read your numbers out loud, per field, as counts.

- [ ] Both variants scored on the same ten records with the same scorer, and
      both tables saved to disk
- [ ] Per-field movement reported, not one overall number
- [ ] Any field that got **worse** named, with a diagnosis. This is the most
      valuable observation available today.
- [ ] The failure lines read, not just the counts, so you can say whether an
      error disappeared or changed shape
- [ ] The input token cost of the example block stated per call and per
      thousand calls
- [ ] Your prediction from checkpoint 1 confronted with the result in
      writing, including if it was wrong

## Before you leave

- [ ] Code committed and pushed
- [ ] `artifacts/goldset.json` written, with ten cases, each carrying an
      `expected_behavior` sentence and a language tag
- [ ] `python -m project.verify` passes
- [ ] `DECISIONS.md` has all six entries, and every number carries its model
      name and run date
- [ ] The sensitivity variant attempted, or explicitly deferred with a note
      saying why

## Homework, before week 3

- [ ] Both variants run live, if you only used the recording in the session
- [ ] The gold set finished. Every `expected_behavior` is a sentence a
      colleague could grade against, not a label.
- [ ] One sentence in `DECISIONS.md` naming the thing your scorer cannot
      currently detect

## What "done" means here

The deliverable is the comparison, not the two extractors. A student who
finishes with two working variants and no scores has not done the exercise.
A student whose few-shot variant scored worse, who can say which field moved
and why, and who decided not to ship it, has done it completely.
