# Judge rubric template, with anchors

BPINFOR-132, week 10. Course-wide artefact: use it again in weeks 11, 12, and
in your project report.

Fill one copy of this template per criterion. Attach the completed copies to
your project report. A judge whose rubric is not written down is an opinion,
and an opinion cannot be a build gate.

## Why anchors

An unanchored judge parks almost everything in the middle of the scale. Ask a
model for "overall quality out of ten" and you will get sixes, sevens, and
eights forever, which means the metric cannot detect a regression, which means
the metric is decoration.

An anchor is a sentence saying what a given score looks like, concrete enough
that two people reading the same output would assign the same number. Writing
anchors is where the real work is. If your group cannot agree on what a 0.5
looks like, the criterion is not yet defined, and no amount of prompt
engineering will define it for you.

Validate the anchors with humans before you validate the judge. Huyen's
instruction, which this course adopts: if humans find the rubric hard to follow,
refine the rubric rather than the prompt.

## Template, one copy per criterion

### 1. Identity

| Field | Value |
| Criterion name | |
| One sentence definition | |
| Why this criterion and not a cheaper check | |
| Scale | binary 0 or 1, or 0 / 0.5 / 1, or 1 to 5. State it and do not change it mid-semester. |
| Pass threshold, and what happens on a fail | |
| Judge model, and its family | |
| Model under test, and its family | |
| Different families? | yes / no, and if no, the reason |
| Rubric version, date, and git commit | |

### 2. What the judge sees

List exactly the fields passed to the judge, in order. Anything not on this
list is invisible to it, and anything on it can bias it.

| Field | Included | Note |
| The question | | |
| The answer under test | | |
| The retrieved passages | | |
| A reference answer | | omit for reference-free criteria |
| The answer length | | see the verbosity control below |
| Which model produced the answer | | almost always omit, it invites self preference |

### 3. Evaluation steps, as a procedure

Write the steps a careful human would follow. Not a description of the
criterion, a procedure. Three to five steps.

1.
2.
3.
4.

### 4. Anchors

One row per point on your scale. Each anchor gets a sentence and a real example
from your own golden set, copied verbatim.

| Score | What it looks like | Example from our set (case id) |
| 1 | | |
| 0.5 | | |
| 0 | | |

Edge cases, decided in advance so a disagreement is visible rather than silent:

- A correct answer supported by a passage the model did not cite:
- An answer that is right but longer than it needs to be:
- A refusal on a case that could have been answered:
- An answer that is partly right and partly invented:

### 5. Bias controls

| Bias | What it does | Control we applied | Evidence we recorded |
| Position | Favours whichever answer is shown first in a pairwise comparison. Note that humans are the opposite way round and favour the last. | Every pair run twice with the order swapped, results kept only where both orderings agree | Disagreement count, out of N pairs |
| Verbosity | Prefers the longer answer. Judges have preferred longer answers of about 100 words with factual errors over shorter correct ones of about 50. | Length cap stated in the rubric, and the rubric anchored on traceable evidence rather than on completeness | Correlation between answer length and score |
| Self preference | Favours text the judge itself produced. Measured at about 10 percent for one model and about 25 percent for another. | Judge model from a different family from the model under test. Never let a model grade its own output on a gate. | Both model names, recorded next to every score |
| Inconsistency | The same judge on the same input can score differently on a rerun. | Sampling settings fixed, worked examples in the prompt, judge scored on repeated runs like any other component | Score variance across K reruns on a fixed slice |

Note the cost of the second control against inconsistency. Including worked
examples raised one reported judge's consistency from 65 percent to 77.5 percent, and quadrupled the prompt spend. Also note that higher consistency is not
higher accuracy: a judge can be consistently wrong.

### 6. Human validation, the control that is not optional

| Field | Value |
| Number of cases labelled by hand | at least 10 in the session, and write the figure down, because every number below has to be read against it |
| Labels written before any judge score was seen? | yes / no. If no, the number below means nothing. |
| Who labelled them | |
| Plain agreement | |
| Cohen's kappa | |
| Cases where we disagreed | list the case ids |
| For each disagreement, who was right | |
| What we changed as a result | |

If you agree with the judge on every labelled case, suspect the sample rather
than celebrate the judge. It usually means every labelled case was easy.

Ten labels is a session-sized sample and not a defensible one. On ten cases a
single disagreement moves plain agreement by ten points and moves the kappa a
long way, so both numbers are indicative rather than conclusive. Never quote
either of them without the sample size next to it, and never present two kappas
computed on ten labels each as a difference. A judge you intended to ship would
be validated against a few hundred cases, sampled from real traffic rather than
from your own golden set, and labelled by at least two people so that the
humans can be checked against each other before the judge is.

### 7. Cost

| Field | Value |
| Judge calls per full regression run | cases x criteria x K |
| Euros per full run | |
| Seconds per full run | |
| How often we intend to run it | on every commit, nightly, or before release |
| What we would drop first if the budget halved | |

## Worked example, groundedness

Reproduced here as a standard, not as an answer to copy.

**Criterion.** Groundedness. Every factual claim in the answer is traceable to a
sentence in the retrieved passages.

**Why not a cheaper check.** A deterministic check can verify that a cited chunk
id was actually retrieved, and week 7 already did that. It cannot verify that
the sentence in the answer follows from the text of the passage. That step needs
a reader.

**Scale.** 0, 0.5, 1. **Threshold** 0.8, so only a 1 passes. **Judge** a model from
a different family from the generator.

**Evaluation steps.**

1. List each factual claim in the answer separately.
2. For each claim, find the exact sentence in the passages that supports it.
3. A claim supported by no sentence is unsupported. Length is irrelevant.
4. A citation naming a passage that is not present is an invented citation.

**Anchors.**

| Score | What it looks like |
| 1 | Every claim is traceable to a quoted sentence in a supplied passage, and every citation names a passage that was supplied. |
| 0.5 | At least one claim is plausible and consistent with the passages but cannot be traced to a specific sentence. No claim contradicts a passage. |
| 0 | Any claim contradicts a passage, or any citation names a passage that was never supplied, or the answer draws on knowledge not present in the passages. |

**Edge cases.** A correct answer that cites nothing scores 0.5, not 1, because
groundedness is about traceability rather than about correctness. A refusal on
an answerable case is not scored here at all: it is a refusal failure and the
deterministic check catches it.

**The trap this rubric is built to avoid.** Without step 3 the judge silently
rewards long, confident answers. Without the second half of the 0 anchor it
never notices an invented citation, which is the single most alarming failure a
retrieval system has.

## The threshold is part of the rubric, and it was measured

Added August 2026, after the lab was rebuilt and the numbers came in.

A rubric describes how to score. It is only half an instrument until you say
where the line is, and the line turns out to matter more than it looks.

On the twelve hand-labelled cases in `judge.py`, with the grounding
criterion in `CRITERIA`, the judge agreed with every human label. Sweeping
the threshold over the same, unchanged scores:

| threshold | agreement | false pass | false fail |
| 0.15 | 0.50 | 6 | 0 |
| 0.25 | 0.67 | 4 | 0 |
| 0.35 | 0.75 | 3 | 0 |
| 0.45 | 1.00 | 0 | 0 |
| 0.50 | 1.00 | 0 | 0 |
| 0.55 | 1.00 | 0 | 0 |
| 0.65 | 0.92 | 0 | 1 |
| 0.75 | 0.83 | 0 | 2 |

Three things to take from that into your own rubric.

Perfect agreement holds on a band one tenth wide. The default of 0.5 sits in
the middle of it, and nobody chose that, it is what the library ships. A
rubric that names a criterion and not a threshold has left the most fragile
decision to a default.

The two errors are not symmetric and they do not appear together. Everything
below the band is a false PASS, a green gate on an invented answer.
Everything above is a false fail, which costs a reviewer's attention and
nothing worse. So pick the side of the band you would rather be wrong on,
and write down why, in terms of what the consequence is for your system
rather than in terms of the metric.

And validate before you tune. The order matters: labels first, then scores,
then the threshold. Choosing a threshold to make agreement look good on
cases you have already seen scored is fitting to your test set, and it is
the most common way an evaluation quietly stops being one.
