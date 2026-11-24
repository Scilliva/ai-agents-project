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
|---|---|
| Criterion name | Answer groundedness against a reference answer. |
| One sentence definition | Check whether the answer addresses the question using only facts in the reference answer. |
| Why this criterion and not a cheaper check | A simple check can compare numbers or words. It cannot judge whether the whole answer follows the reference. |
| Scale | binary 0 or 1, or 0 / 0.5 / 1, or 1 to 5. State it and do not change it mid-semester. Our implemented GEval scale is 0 to 1, including decimal scores. The rows below describe low, middle, and high scores. |
| Pass threshold, and what happens on a fail | At least 0.50 passes. A lower score fails the evaluation and needs review before the answer is accepted. |
| Judge model, and its family | Local `qwen3:4b-instruct`, Qwen family. |
| Model under test, and its family | This run scores the twelve supplied example answers. Their generating model is not recorded. My app uses `qwen2.5:7b`, also Qwen, but its actual answers were not scored in this judge run. |
| Different families? | yes / no, and if no, the reason. For the supplied answers, the source model is unknown. The app and judge are both Qwen models chosen for the course. A different-family judge has not been tested. |
| Rubric version, date, and git commit | Version 1, 2026-11-24. Base commit `f43bc42`, with uncommitted Week 10 changes. This rubric records the existing experiment after the run. |

### 2. What the judge sees

List exactly the fields passed to the judge, in order. Anything not on this
list is invisible to it, and anything on it can bias it.

| Field | Included | Note |
|---|---|---|
| The question | Yes, first. | Passed as INPUT. |
| The answer under test | Yes, second. | Passed as ACTUAL_OUTPUT. |
| The retrieved passages | No. | This judge uses a reference answer. The separate RAGAS exercise uses passages. |
| A reference answer | Yes, third. | omit for reference-free criteria. Our run passes EXPECTED_OUTPUT. |
| The answer length | No separate length field. | see the verbosity control below. The judge can still see how long the answer is. |
| Which model produced the answer | No. | almost always omit, it invites self preference. This information is not passed to our judge. |

### 3. Evaluation steps, as a procedure

Write the steps a careful human would follow. Not a description of the
criterion, a procedure. Three to five steps.

1. Read the question and the reference answer.
2. Check whether the actual answer addresses the question.
3. Check each factual claim against the reference. Look for invented fees, deadlines, offices, or documents.
4. Give a score from 0 to 1. Prefer a correct but incomplete answer over one with invented facts. Use 0.50 as the pass cutoff.

### 4. Anchors

One row per point on your scale. Each anchor gets a sentence and a real example
from your own golden set, copied verbatim.

| Score | What it looks like | Example from our set (case id) |
|---|---|---|
| 1 | The answer addresses the question and all its facts match the reference. | L-01, supplied calibration set: "The residential parking vignette costs 60 EUR per year and is applied for at the Bierger-Center with proof of residence." Recorded score was 1.00. |
| 0.5 | The answer gives correct information but leaves out part of what was asked. | L-05, supplied calibration set: "The vignette costs 60 EUR per year." This illustrates an incomplete answer. Its recorded score was 0.60, rather than exactly 0.50. |
| 0 | The answer is unrelated to the question or gives no supported answer. | L-03, supplied calibration set: "The library is open on Saturday mornings." Recorded score was 0.00. |

Edge cases, decided in advance so a disagreement is visible rather than silent:

- A correct answer supported by a passage the model did not cite: It can pass if its facts match the reference. This criterion does not require citations.
- An answer that is right but longer than it needs to be: Extra length earns no extra credit. Any added facts still need support from the reference.
- A refusal on a case that could have been answered: Fail. L-07 refuses an answerable question and scored 0.20.
- An answer that is partly right and partly invented: Fail if it adds an invented fee, deadline, office, or document. A correct part does not cancel out the invented part.

### 5. Bias controls

| Bias | What it does | Control we applied | Evidence we recorded |
|---|---|---|---|
| Position | Favours whichever answer is shown first in a pairwise comparison. Note that humans are the opposite way round and favour the last. | Every pair run twice with the order swapped, results kept only where both orderings agree  Our run scores one answer against a reference. We did not run swapped pairs. | Disagreement count, out of N pairs  Our run: no order-swap disagreement count was measured. |
| Verbosity | Prefers the longer answer. Judges have preferred longer answers of about 100 words with factual errors over shorter correct ones of about 50. | Length cap stated in the rubric, and the rubric anchored on traceable evidence rather than on completeness  Our criterion favours correct incomplete answers. No length cap was added. | Correlation between answer length and score  Our run: no length-score correlation was measured. |
| Self preference | Favours text the judge itself produced. Measured at about 10 percent for one model and about 25 percent for another. | Judge model from a different family from the model under test. Never let a model grade its own output on a gate.  Our supplied answers have no recorded source model, so family separation was not verified. | Both model names, recorded next to every score  Our run records the judge model. The source model for these examples is unknown. |
| Inconsistency | The same judge on the same input can score differently on a rerun. | Sampling settings fixed, worked examples in the prompt, judge scored on repeated runs like any other component  Our run used K=1 per case. We did not add worked examples or repeat cases to test score stability. | Score variance across K reruns on a fixed slice  Our run: variance was not measured. The threshold sweep reuses scores and does not test repeatability. |

Note the cost of the second control against inconsistency. Including worked
examples raised one reported judge's consistency from 65 percent to 77.5 percent, and quadrupled the prompt spend. Also note that higher consistency is not
higher accuracy: a judge can be consistently wrong.

### 6. Human validation, the control that is not optional

| Field | Value |
|---|---|
| Number of cases labelled by hand | at least 10 in the session, and write the figure down, because every number below has to be read against it. Our run used 12 supplied human-labelled cases. |
| Labels written before any judge score was seen? | yes / no. If no, the number below means nothing. Yes for the supplied course labels. My own review of L-09 happened after the live run, and did not change those recorded labels. |
| Who labelled them | The course supplied the twelve labels. I reviewed L-09 and would mark it fail because it leaves out the appointment requirement. |
| Plain agreement | 12/12, or 100%, against the supplied labels at threshold 0.50. This is a small sample. |
| Cohen's kappa | 1.00 on the same twelve cases. The judge and supplied labels matched on five passes and seven fails. |
| Cases where we disagreed | list the case ids. My review disagreed with L-09. The judge had no disagreements with the original twelve labels at 0.50. |
| For each disagreement, who was right | For L-09, I would choose fail. Someone could put their trash out without booking and it would not be collected. The course accepts it because the day is correct and nothing is invented. |
| What we changed as a result | I recorded the disagreement in the decisions file. The original label and 0.50 cutoff were kept for the experiment. |

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
|---|---|
| Judge calls per full regression run | cases x criteria x K. Our run was 12 cases x 1 criterion x 1 repeat = 12 case evaluations. GEval can use multiple local model requests per case. |
| Euros per full run | No hosted API fee. Electricity and hardware costs were not measured. |
| Seconds per full run | 57.91 seconds summed across the twelve case timers on 2026-11-23. |
| How often we intend to run it | on every commit, nightly, or before release. I would run the live judge before release or after model or criterion changes. Saved judgments can be checked on every commit. |
| What we would drop first if the budget halved | Run live judging less often and reuse saved scores for routine checks. I would keep the free gates and the human validation. |

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
