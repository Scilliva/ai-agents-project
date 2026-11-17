# Week 10 findings, measured before the session was redesigned

Probe results only. The session rebuild is NOT done yet. Everything below
was run locally against Ollama on the course machine in August 2026, judge
model `qwen3:4b-instruct`, and it is here so the build does not have to
rediscover it.

## Stack, verified present and working

| package | version | note |
| deepeval | 4.1.7 | `OllamaModel` plus `GEval` works against the local endpoint |
| ragas | 0.4.3 | `llm_factory` plus `metrics.collections.Faithfulness`, works locally |
| ollama | 0.6.2 | the separate python package, required by DeepEval |
| langchain-community | 0.3.31 | must stay below 0.4 for RAGAS |
| pytest | 9.1.1 | the harness spine |

API note for the rebuild: `LLMTestCaseParams` now emits a
DeprecationWarning and wants `SingleTurnParams` instead. The starter should
use the new name, or every student's first run prints a warning they will
ask about.

## 1. The judge discriminates, which was not safe to assume

Five outputs against one expected answer, `GEval` with a grounding
criterion, threshold 0.5.

| case | score | verdict | seconds |
| the expected answer itself | 1.00 | pass | 11.1 |
| correct but incomplete | 0.50 | pass | 4.1 |
| invented fee, 85 EUR for 60 | 0.40 | fail | 3.2 |
| honest refusal | 0.00 | fail | 3.6 |
| off topic | 0.00 | fail | 3.0 |

Four distinct scores across five cases, spanning the full range. That
matters because week 7 established the rule that a metric which cannot vary
on your data is not measuring your system, and a judge pinned at 0.9 is the
classic instance. This one is not pinned, so it is worth building on.

Note the third row is the one that earns the judge its place: an invented
fee is the failure the whole course cares about, and the judge caught it and
named it.

## 2. The judge is deterministic here, and that is worth stating

The borderline case, right fee and wrong place, run five times:

```
scores    [0.40, 0.40, 0.40, 0.40, 0.40]
verdicts  fail, fail, fail, fail, fail
reason    identical every time, "introduces the term 'citizen portal'
          which is not present"
```

No flip, no spread. DeepEval drives the judge at temperature 0, so a single
judged score IS reproducible on this stack, which is the opposite of what a
session about nondeterminism would assume.

Design consequence for the rebuild: do NOT build the session around judge
flakiness, because on this stack it does not flake. The honest tension to
build on instead is cost and necessity. The judge takes about three seconds
per case against microseconds for a deterministic check, so the question a
student has to answer is not "is my judge stable" but "which cases actually
need one".

The reasoning quality is also good enough to show in the room. It found the
one substituted noun in a sentence that was otherwise correct.

## 3. What is available to reload

Week 10 is the first session that consumes rather than produces.

| artifact | contents |
| `artifacts/goldset.json` | 58 cases, `week_added` 2, 3, 4, 5, 7 |
| `artifacts/traces.jsonl` | 77 traces, weeks 5, 8, and 9 |
| `artifacts/week07_retrieval.json` | per question ranks, both retrievers |
| `artifacts/week08_faults_{baseline,hardened}.json` | the fault matrix, both configurations |
| `artifacts/week09_{extractions,break,untrusted}.json` | the vision tables |

Note the gold set keys its week as `week_added`, not `week`, and that week 9
has not contributed cases to it yet. Adding them is a candidate TODO for the
rebuilt session, and it would take the set to roughly 63.

## 4. RAGAS discriminates too

`Faithfulness` from `ragas.metrics.collections`, against the same local
model, three answers over one retrieved context:

| case | faithfulness | seconds |
| grounded in the context | 1.00 | 13.5 |
| one invented fee, 85 EUR for 60 | 0.50 | 8.9 |
| wholly invented | 0.00 | 6.9 |

Three distinct values over the full range. The API shape that works on
0.4.3, since it moved twice in a year:

```python
client = AsyncOpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama")
llm = llm_factory("qwen3:4b-instruct", provider="openai", client=client)
await Faithfulness(llm=llm).ascore(user_input=..., response=...,
                                   retrieved_contexts=[...])
```

`ascore` takes keyword arguments and returns an object with `.value`, and
`langchain-community` must stay below 0.4 or the import fails.

## 5. All four reliability dimensions are computable from the traces

Checked against the 62 recorded traces rather than assumed.

| dimension | what carries it | available |
| consistency | repeated runs of one `case_id` | yes, week 8 has 2 per case and week 9 has 3 |
| robustness | `conditions.settings` varying while `case_id` is fixed | yes, week 8 `fault`, week 9 `variant` |
| predictability | `steps[].detail` and `notes` against `outcome` | yes |
| safety | `outcome` of `refused` and `blocked`, plus week 9 `notes.verdict` | yes |

So the Trace contract needs no new field, which is the answer that lets
week 10 be an analysis session rather than an instrumentation session.

## 6. A defect found in the reference artifacts, and fixed

The recorded week 9 traces carried the run condition under two different
keys: `settings.scale` in traces written before the perturbation refactor
and `settings.variant` in traces written after. Same fact, two homes, and
any harness grouping by condition would have silently produced two groups
where there is one.

Fixed by dropping the 30 stale week 9 traces and regenerating them from
replay, so `traces.jsonl` now holds 62 records with exactly one spelling per
condition. Worth keeping as a teaching example: this is precisely the drift
week 8's `drift` fault injects on purpose, found for real in the course's
own artifacts.

## Still to probe

- Judge agreement against hand labels on genuinely ambiguous cases. The five
  in section 1 were all obvious, and the judge agreed with the intended
  verdict on all five, which tells you the easy cases are easy and nothing
  more. This is the session's own block 2 exercise.
