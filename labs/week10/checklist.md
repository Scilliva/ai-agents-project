# Week 10 checklist

Tick these as you go. The in-session list is what a demonstrator will ask
you about while walking the room.

## In session

### Block 1, the free layer (8 to 40)

- [ ] Your own `artifacts/traces.jsonl` loads, and you know how many traces
      you have and from which weeks
- [ ] TODO 1a, consistency, groups by case AND condition. Check one group by
      hand before you trust the number.
- [ ] TODO 1b, robustness, and you can say why it differs from consistency
      in one sentence
- [ ] A dimension with no evidence returns None, not 0.0, and you can say
      why that distinction matters
- [ ] TODO 2a and 2b done, and safety counts a refusal in the NUMERATOR
- [ ] `01_free.py` runs and writes `artifacts/week10_free.json`
- [ ] You can name the week with the best accuracy and say why its other
      columns are empty
- [ ] You have looked at the case ids in weeks 5 and 8 and can say what went
      wrong when they were named

### Block 2, the judge (40 to 70)

- [ ] `python 02_judge.py` STARTED live at the top of the block
- [ ] You read all twelve hand labels and disagreed with at least one, in
      writing, before running the judge
- [ ] TODO 3a and 3b done, and `build_metric` imports DeepEval INSIDE the
      function so block 1 does not need it
- [ ] TODO 4 done, and your `validate` RECOMPUTES the verdict from the score
      and the threshold rather than reading it back from the recording
- [ ] You checked TODO 4 the way the docstring says: if the threshold sweep
      prints identical rows, your validate is ignoring the threshold
- [ ] The sweep run, and you can name the band where agreement is perfect
- [ ] You can say which of false pass and false fail is worse here, and why

### Block 3, the gates (70 to 85)

- [ ] TODO 5a, 5b, 5c done, and `pytest -q` is green
- [ ] `pytest -q -m "not judged"` runs with no model calls, and you timed it
- [ ] You broke each gate on purpose and watched it fail. A gate you have
      never seen fail is not a gate.
- [ ] None of your gates asserts a number this week happened to produce

### Close (85 to 90)

- [ ] `DECISIONS.md` section written, with conditions beside every number
- [ ] Committed and pushed

## Homework

- [ ] Your week 9 cases added to the gold set, which currently stops at
      week 7, each with one line saying what it is for
- [ ] `pytest -m "not judged"` wired into a pre-commit hook or your CI, with
      its wall clock recorded
- [ ] One paragraph: which of your metrics you would let block a release,
      and which you would only let raise a warning

## The three things a demonstrator will ask

1. Show me a dimension that returns None, and tell me why that is not zero.
2. Set your threshold to 0.15 and run the gates. Which one catches it, and
   what does the failure message tell you?
3. Your judge agrees with the labels. Convince me that is evidence.
