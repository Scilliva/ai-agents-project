# Week 1 checklist

## Checkpoint 1, after the first call

Six items. Do not move to block 3 until all six are true.

- [ ] `00_preflight.py` reports every line green, or you know which line is
      red and why. The context window check is the one that matters: a
      failure there means the model is reserving about eleven times the
      memory it needs.
- [ ] A call returns text, and you printed the text
- [ ] You printed the finish reason and can say what your program would do
      differently if it were the truncation reason
- [ ] You printed both token counts and can say which of the two you control
- [ ] You printed the elapsed time and can say which part of it a user feels
- [ ] `python -m project.verify` reports one record in `traces.jsonl` and no
      contract failures

## Checkpoint 2, what the numbers showed

Six items. Be ready to say your numbers out loud, as counts rather than
percentages.

- [ ] The recording has been run with `--replay --full` and you have the
      eight-cell table in front of you
- [ ] Your own two cells have been run live, and the two `distinct` columns
      are side by side
- [ ] You can name the cell that returns a single answer at temperature 1.0
      and explain why that one
- [ ] You can name which cells a test asserting exact string equality would
      pass on, and which it would fail on
- [ ] Your variance table is saved to `artifacts/week01_variance.json`, not
      just printed on screen
- [ ] The sentence from TODO 6 is written in `DECISIONS.md`, and it does not
      say "the model is random"

**If your live numbers exactly match the recording on every cell**, that is
plausible and worth a second look rather than a celebration. Check that you
actually ran without `--replay`. This is the first instance of a rule that
runs all semester: a result that comes out exactly as expected is a result
worth double-checking, because the most common cause is that you measured
the wrong thing.

## Before you leave

- [ ] Code committed and pushed
- [ ] `DECISIONS.md` has all five entries from the template
- [ ] Every number in it carries its model name and the date of the run
- [ ] `python -m project.verify` passes
- [ ] The homework sweep has been started, or explicitly deferred with a note
      saying why

## Homework, before week 2

- [ ] `02_variance.py --full` run live, and the eight-cell table replaces
      the two-cell one in `DECISIONS.md`
- [ ] The optional models pulled, so week 9 does not begin with a download
- [ ] `project_spine/README.md` read, and `project/contracts.py` skimmed

## A note on what "done" means here

Every checkpoint in this course asks what you measured and what you
concluded, never whether the code runs. A student who finishes all four
scripts and cannot say what the cold start implies for week 3 has not
finished block 4. A student whose block 3 crashed but who can explain the
recording has done most of the session.
