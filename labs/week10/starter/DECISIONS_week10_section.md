# Week 10, the evaluation harness

Copy this into your project `DECISIONS.md` and fill it in. In week 13 this
becomes a section of your report you do not have to write.

This is the first week whose numbers are ABOUT your other weeks, so every
figure needs to say which runs it covers and when they were recorded.

## Conditions

- Traces covered: how many, from which weeks, recorded when:
- Judge model and version:
- Judge threshold:
- Harness versions (deepeval, ragas, pytest):
- Run date:

## The free layer

| week | runs | accuracy | consistency | robustness | predictability | safety |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |

Which week has the best accuracy, and what do its other columns say:

Which week has the best predictability, and what does its accuracy say:

In one sentence: what ranking these systems by accuracy alone would have
told you, and why it would have been wrong:

### The n/a cells

List every dimension that returned None, and for each one say whether it is
an ABSENCE (you have no evidence yet) or a DEFECT (you could have had
evidence and your instrumentation threw it away).

| week | dimension | absence or defect | what would fix it |
|  |  |  |  |

The case ids in weeks 5 and 8 encode something they should not. Say what,
and what it cost you:

## The labels

The label you disagreed with, and your reasoning:

Whether you changed the label or kept it, and why:

## The judge

Agreement with the hand labels at your chosen threshold:

| | human pass | human fail |
| judge pass |  |  |
| judge fail |  |  |

The threshold sweep:

| threshold | agreement | false pass | false fail |
|  |  |  |  |

The band where agreement is perfect:

Where your threshold sits inside that band, and who chose it:

Which of false pass and false fail is worse for YOUR system, in one sentence
that names the consequence rather than the metric:

## Cost

| layer | model calls | wall clock | can it run on every commit |
| deterministic checks |  |  |  |
| the four dimensions |  |  |  |
| the judge |  |  |  |

What you would put in a pre-commit hook, what in CI, and what you would run
only before a release:

## The gates

| gate | what it protects | what a failure would mean |
|  |  |  |
|  |  |  |
|  |  |  |

For each gate, how you made it fail on purpose:

Any gate that asserts a number from this week rather than a property that
should hold for any healthy version, and why you kept it anyway:

## What you will not claim

One paragraph. Name the things your harness does NOT measure, and what
somebody would have to do to find those failures. This paragraph is worth
more marks than a table of good scores, because it is the part that shows
you know where your evidence stops.
