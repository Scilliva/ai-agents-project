# Week 5 checklist

## Checkpoint 1, plan then propose

Six items. Do not move to block 2 until all six are true.

- [ ] The test suite run once on a fresh copy, and you can name the failing
      test and the module it points at
- [ ] A plan generated and **printed in full** before anything was applied
- [ ] `validate_plan` implemented with at least three checks, and one
      deliberately broken plan shown to fail
- [ ] A fix proposed as a structured object, not as free-form editing
- [ ] `apply_fix` seen refusing at least one thing: a test file, a line that
      is not there, or an ambiguous line
- [ ] The suite verified by `run_tests` rather than by the agent's claim of
      success

**If your nested plan schema worked**, say so at the checkpoint, because the
reference run says it does not. Then check you are on the model the brief
names.

## Checkpoint 2, was the second agent worth it

Six items. Counts out of three runs, never impressions.

- [ ] All three architectures run on the same task with the same verifier
- [ ] The table reported: green out of three, tokens, and seconds each
- [ ] One sentence on why the baseline fails that is **not** "the model is
      too small"
- [ ] The reviewer's verdict logged for every run, with its reason
- [ ] Extra cost of the reviewer computed, as tokens and seconds per run
- [ ] One sentence saying which of the three you would ship and what
      evidence would change your mind

## Before you leave

- [ ] Code committed and pushed
- [ ] `python -m project.verify` passes, gold set at 46 cases
- [ ] `DECISIONS.md` has all six entries, with the model name and run date
- [ ] Entry 6, what your verifier cannot catch, is written

## Homework, before week 6

- [ ] All three architectures run live, three times each
- [ ] Task B, the refactoring, attempted, and the gap between architectures
      reported
- [ ] One sentence on whether the planner earned its cost on task B, given
      that it did or did not on task A

## What "done" means here

The deliverable is the comparison and the diagnosis. A student whose fixer
goes green and who cannot say why the baseline did not has not done the
session. A student who reports that the reviewer did not help (in the recording
it made things worse), explains that a free deterministic verifier already catches what it would catch, and
names the case where that stops being true, has done it completely.

A negative result about the second agent is the expected result here, and
reporting it honestly scores above claiming a win.
