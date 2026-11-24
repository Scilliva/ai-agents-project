# Week 10, the evaluation harness

Copy this into your project `DECISIONS.md` and fill it in. In week 13 this
becomes a section of your report you do not have to write.

This is the first week whose numbers are ABOUT your other weeks, so every
figure needs to say which runs it covers and when they were recorded.

## Conditions

- Traces covered: how many, from which weeks, recorded when:
  I ran `01_free.py` as instructed. The table compares the 58 lab runs it reported from my project's `artifacts/traces.jsonl`. Week 5 has 22 runs from 2026-10-18, Week 8 has 16 from 2026-11-12, and Week 9 has 20 from 2026-11-17. The separate gate tests use the full 540-run project log.
- Judge model and version:
  `qwen3:4b-instruct`, locally on Apple M4 Mac with 16 GB RAM. The Ollama Python package was 0.6.3.
- Judge threshold:
  0.50, kept from the starter before the live run.
- Harness versions (deepeval, ragas, pytest):
  DeepEval 4.3.4, pytest 9.1.1, and RAGAS 0.4.4.
- Run date:
  2026-11-23 for the live judge and first free checks. I ran the free report and gates on my own 540 traces on 2026-11-24. The RAGAS exercise also ran on 2026-11-24.

## The free layer

| week | runs | accuracy | consistency | robustness | predictability | safety |
|---|---:|---:|---:|---:|---:|---:|
| 5 | 22 | 0.14 | 0.50 | n/a | 0.00 | 0.00 |
| 8 | 16 | 0.19 | n/a | n/a | 0.77 | 0.54 |
| 9 | 20 | 1.00 | 1.00 | n/a | n/a | n/a |

These rows use the lab runs saved in my project log. I kept the results printed by the supplied script in 01_free.py.

The starter scripts save runs differently across the weeks. In Week 5, replay prints saved results without adding new traces. Week 8 uses offline tools with faults introduced on purpose. In Week 9, both live and replay runs are saved. This is why my Week 9 row has 20 runs, made up of 10 live runs and 10 replays.

The Week 10 consistency calculation groups live and replay runs together. A replay reuses a saved answer, so the 20 runs do not represent 20 fresh model calls. 
I checked the live runs separately too. They still gave 1.00 for accuracy and consistency, on the 10 live runs. 
The table follows the what was expected of us to do in this week and previous ones.
This difference in recording needs to be kept in mind when comparing the weeks.

Which week has the best accuracy, and what do its other columns say:

Week 9 has the best accuracy. All 20 recorded runs (live + replay) succeeded. Consistency is 1.00 because the repeated cases kept the same outcome under the same recorded conditions. 
Robustness is n/a because these runs did not use different conditions for the same case. 
Predictability and safety are empty because there were no unsuccessful runs to actually measure.

Which week has the best predictability, and what does its accuracy say:

Week 8 has the best predictability at 0.77. It flagged 10 of its 13 unsuccessful lab runs. 
Its accuracy is only 0.19, so 3 of 16 runs succeeded. But the lab on purpose introduced faults. 
Week 5 actually has the lowest accuracy, at 0.14, even though the starter's printed explanation says Week 8 does.

In one sentence: what ranking these systems by accuracy alone would have
told you, and why it would have been wrong:

It would make Week 9 look like the most reliable system because all its runs succeeded but actually none of those runs show whether it would notice a problem or stop safely when something goes wrong, while Week 8 actually tested those situations by introducing faults on purpose.

### The n/a cells

List every dimension that returned None, and for each one say whether it is
an ABSENCE (you have no evidence yet) or a DEFECT (you could have had
evidence and your instrumentation threw it away).

| week | dimension | absence or defect | what would fix it |
|---|---|---|---|
| 5 | robustness | defect | Use the same case ID across architectures and put the architecture in conditions. |
| 8 | robustness | defect | Keep the task ID the same across different faults and policies. |
| 8 | consistency | absence | Repeat each case under the same conditions. |
| 9 | robustness | absence | Run the same invoice under different conditions and record them. |
| 9 | predictability | absence | Include unsuccessful runs and check whether they flag a problem. |
| 9 | safety | absence | Include unsuccessful runs and check whether they stop safely. |

The case ids in weeks 5 and 8 encode something they should not. Say what,
and what it cost you:

IDs like `A-baseline-run1` include the architecture and repetition. IDs like `drift-baseline` include the fault and policy. Changing these parts creates a different case ID, so the harness cannot connect the same task across conditions. This is why robustness is empty.

Consistency repeats the same case under the same conditions. Robustness checks the same case under different conditions. 

For the hand check, I looked at `B planner-run1` in my own Week 5 data. 
The same task was run 2 times with the same planner setup. The results were First run — error, Second run — success. 
The outcome changed, so this group was inconsistent. 
There were four groups with repeated runs. Two kept the same outcome every time, giving 2/4 = 0.50, or 50% consistency. A group that fails every time also counts as consistent. 
This score tells me whether the outcome repeats (consistency). I need accuracy to see how often the task actually succeeds.

`None` means there is no evidence to calculate a score. A score of 0.0 means there was evidence from the checks, but none of the qualifying cases actually passed the checks. For safety, refusing to answer counts as a safe stop. The same goes for degraded and blocked outcomes, where the app gives a limited answer or stops the action.

## The labels

The label you disagreed with, and your reasoning:

I disagree with the pass label for L-09. I would mark it as fail. The answer gives the correct collection day but leaves out that an appointment is needed. A person could put their trash out on that day without booking, and it would not be collected. So the AI has misled them, even though it gave the correct day.

Whether you changed the label or kept it, and why:

The course's original pass label was kept for the recorded experiment. This lets me compare the judge with the supplied labels. The reported 12/12 agreement is against those original labels. My own choice for L-09 would be fail because leaving out the appointment changes what the person needs to do.

## The judge

Agreement with the hand labels at your chosen threshold:

The live judge agreed with all 12 human labels at threshold 0.50 on 2026-11-23. These results are saved in `artifacts/week10_judge.json`. This part uses given twelve example answers and labels. My app's actual answers have not been evaluated by this judge yet, because it wasn't asked of us.

| | human pass | human fail |
|---|---:|---:|
| judge pass | 5 | 0 |
| judge fail | 0 | 7 |

The threshold sweep:

| threshold | agreement | false pass | false fail |
|---|---:|---:|---:|
| 0.15 | 0.50 | 6 | 0 |
| 0.25 | 0.67 | 4 | 0 |
| 0.35 | 0.75 | 3 | 0 |
| 0.45 | 1.00 | 0 | 0 |
| 0.50 | 1.00 | 0 | 0 |
| 0.55 | 1.00 | 0 | 0 |
| 0.65 | 0.92 | 0 | 1 |
| 0.75 | 0.83 | 0 | 2 |
| 0.85 | 0.83 | 0 | 2 |

The band where agreement is perfect:

The tested thresholds 0.45, 0.50, and 0.55 all matched every label, so an interval from 0.4 to/including 0.6. An answer passes when its score equals or exceeds the threshold. The sweep reused the same twelve live scores and made no new model calls.

Where your threshold sits inside that band, and who chose it:

I kept 0.50, which was already in the starter. It sits in the middle of the three successful thresholds tested in the sweep and was kept before the live run.

Which of false pass and false fail is worse for YOUR system, in one sentence
that names the consequence rather than the metric:

A false pass is worse because a resident could receive an invented fee, deadline, or application instruction as approved advice, but a false fail wouldn't affect the person as much.

## Cost

| layer | model calls | wall clock | can it run on every commit |
|---|---|---|---|
| deterministic checks | 0 | The local free-check run took 1.48 seconds including startup. Pytest reported 0.09 seconds for the tests themselves. CI will record its own time. | yes |
| the four dimensions | 0 | About 0.00015 seconds for the dimensions and accuracy after loading the reference traces. | yes |
| the judge | 12 cases, each of which may use more than one inference request inside GEval | 57.91 seconds summed across the twelve case timers. | Replay can run on every commit. Live judging can run before release or after changes. |

My local free-check run on 2026-11-24 took 1.48 seconds including startup. There were 5 passed, 1 failed, and 3 deselected. CI will record its own time after I commit and push.

The dimensions timing in the table uses reference traces. The judge timing covers the twelve course examples run on 2026-11-23.

What you would put in a pre-commit hook, what in CI, and what you would run
only before a release:

I would use a pre-commit hook for quick free checks. For this project, I moved them to CI and disabled the hook. The current logs include older errors without warning flags and expected approval holds. Because of how the supplied test counts these runs, the predictability check fails and the hook was stopping commits. CI keeps the failure visible while I continue working. In CI, I would also check the saved judge scores. I would run the live judge before a release or when the model or judging rules change.

## The gates

| gate | what it protects | what a failure would mean |
|---|---|---|
| traces exist | Runs are available. | No traces to evaluate. |
| trace conditions | Model and date are recorded. | Missing context. |
| consistent condition keys | Settings use consistent names. | Different keys within one week and writer. |
| predictability | At least 50% of unsuccessful runs flag a problem. | Too few recognised warnings. |
| unique gold cases | Each case has its own ID. | Duplicate IDs. |
| growing gold set | Cases cover at least three weeks. | Limited coverage. |
| judge agreement | At least 90% agreement with human labels. | Agreement is too low. |
| no false passes | Human-failed answers stay failed. | An unacceptable answer passed. |
| threshold stability | Agreement changes by at most 5 percentage points at threshold ±0.05. | A small cutoff change has too much effect. |

On my own 540 traces on 2026-11-24, 8 gates passed and 1 failed. The free run had 5 passed, 1 failed, and 3 deselected. All nine had passed earlier using the professor's reference traces.

Predictability failed because only 38 out of 104 unsuccessful runs had the warning flags this check looks for. That's 36.5%, below the 50% needed to pass. Part of this comes from how the exercises were set up. The supplied Week 5 code can save an error without a warning flag. The app also counts a request held for approval as unsuccessful, even when stopping was the right thing to do. That approval decision does not count as a warning. So the earlier logs do not always save what Week 10 expects, even though our calculation follows the given rules.

The hook was blocking commits on this known issue. I disabled it and moved the checks to CI, where the failure stays visible.

For each gate, how you made it fail on purpose:

I used temporary bad inputs to check that each gate would catch a problem. Every gate failed as expected. After changing the inputs back, all nine passed using the professor's reference traces, my gold set, and the saved judge scores.

| gate | deliberate change |
|---|---|
| traces exist | Used an empty trace list. |
| trace conditions | Removed the model and run date. |
| consistent condition keys | Used different settings keys within the same week's lab runs. |
| predictability | Used an error with no warning flag. |
| unique gold cases | Gave two cases the same ID. |
| growing gold set | Used cases from only one week. |
| judge agreement | Lowered the cutoff to 0.15. Only 6 out of 12 labels matched. |
| no false passes | Used the 0.15 cutoff. Six answers marked fail by a human passed. |
| threshold stability | Used a cutoff of 0.40. Moving it to 0.45 changed agreement from 75% to 100%. |

Any gate that asserts a number from this week rather than a property that
should hold for any healthy version, and why you kept it anyway:

None of the gates needs the exact scores we got this week. They check minimum requirements, like at least 90% agreement and no false passes. A better score would still pass. If no judge scores are saved, the judged tests are skipped. If only some are saved, the agreement gate fails.

Missing conditions, duplicate IDs, low predictability, and false passes would block a release. I would use accuracy, robustness, and missing reliability scores as warnings while I add more cases.

## What you will not claim

One paragraph. Name the things your harness does NOT measure, and what
somebody would have to do to find those failures. This paragraph is worth
more marks than a table of good scores, because it is the part that shows
you know where your evidence stops.

These results are not enough to say the whole agent is reliable. The free report uses my own runs, but the judge and RAGAS only checked the supplied examples. My own runs still failed the predictability gate, because of how the project was set up. Accuracy also depends on the outcome saved in each trace. It does not check every amount against the invoice image. The amounts could add up and still be read wrong. The agent could also repeat the same mistake and get a good consistency score. To find these problems, I would test more real questions, invoice photos, and inputs with faults added on purpose. I would save my actual answers with the passages they used and ask people to check them independently. I would also repeat the live judging to see whether the scores change.

## Optional RAGAS exercise

I ran the supplied RAGAS exercise on 2026-11-24 with RAGAS 0.4.4 and local `qwen3:4b-instruct`. It used the professor's fixed passages and answers.

| answer | faithfulness |
|---|---:|
| correct fee and office | 1.00 |
| invented fee, correct office | 0.50 |
| completely invented answer | 0.00 |

Faithfulness checks whether the passages support the answer. The judge compares it with the expected answer. An answer can follow a wrong passage and still get a good faithfulness score. In Week 7, the retrieval check caught Q05 missing the required sections in its top five results. Faithfulness alone would not catch that. To score my own answers, I would need their questions and the exact passages used in the same run.
