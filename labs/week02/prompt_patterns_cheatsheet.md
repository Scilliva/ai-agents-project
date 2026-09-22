# Prompt pattern cheat sheet

BPINFOR-132, week 2. One page, kept open while you write prompts. Every entry
names the failure it prevents, because a pattern you cannot attach to a
failure is a habit rather than a technique.

Sources: AIE-Huyen chapter 5 (clear and explicit instructions, in-context
learning, context length and efficiency) and ADP-Gulli Appendix A (advanced
prompting techniques). Anything here that describes a product feature rather
than a principle is dated August 2026 and should be checked against current
provider documentation.

## 1. Structure

| Pattern | What it prevents |
| Four parts: task, context, output contract, rules | A prompt that is complete by accident and incomplete under a case you did not think of |
| Instruction constant, in the system message | Paying full input price on every call, and having three copies of the prompt to edit |
| Stable text first, variable text last | Breaking the cacheable prefix, which is a cost bug that is invisible until the invoice |
| Evidence delimited with tags | The model reading your data as an instruction, which is prompt injection (week 12) |
| Prompt in a named module with a version identifier | A regression that nobody can trace to a change |

## 2. Instructions

| Pattern | What it prevents |
| Closed label set, stated in full | An output your program has no branch for, and an accuracy you cannot compute |
| The absent case specified explicitly | An invented value where a null belonged |
| Output length capped | A cost ceiling discovered rather than chosen |
| Ask for a verbatim quotation | An unverifiable claim. A quoted span is checkable by string search, for free. |
| Say what is out of scope, and what to do then | The model improvising at the edge of the task. Weak on its own, layered in week 11. |
| Positive form: say what to do, not only what not to do | An instruction the model satisfies while missing the intent |

## 3. Examples, in-context learning

| Pattern | What it prevents |
| Three to five examples, chosen for the boundary | Twelve examples that all demonstrate the case that already worked |
| Labels balanced across the set | The model inheriting your example distribution as a prior |
| One example showing the null convention | A convention that words alone repeatedly fail to fix |
| One example in each language your users actually write in | Silent degradation on most of the traffic |
| Examples read together with the instruction, looking for contradictions | Two specifications in one prompt, chosen between per call |
| Examples never drawn from the evaluation set | A score that measures copying rather than generalisation |
| Example order varied and measured | An ordering effect you did not intend and cannot see |

## 4. Reasoning and intermediate state

| Pattern | What it prevents |
| Chain-of-thought where a wrong answer is expensive | Paying output tokens for a trace nobody inspects |
| The thought in a schema field, not in prose | Parsing reasoning out of an answer with a regular expression |
| The thought length capped | An unbounded token bill on a field with no downstream consumer |
| Treat the trace as a debugging signal, not as an explanation | Believing a generated narrative is a log of the computation |
| On reasoning-tuned models, set the reasoning budget rather than the phrase | Prescribing a reasoning path that the model was going to do better on its own |

As of August 2026, the major providers expose reasoning as a per-call budget
on their reasoning-tuned models, and the older advice to spell out the steps
in words has weakened. Sources disagree about how far. Settle it on your task
with your harness, not with a blog post.

## 5. Output contracts

| Pattern | What it prevents |
| Pydantic schema, not a prose description of a format | A format that drifts between the prompt and the parser |
| Provider-side constrained generation, and validation anyway | Trusting a feature that can be unavailable, swapped, or out of date |
| A content check against the evidence, on top of the shape check | Believing that a valid object is a correct one |
| Assistant prefill with the opening brace, where supported | "Here is the extraction:" in front of your JSON |
| A decided behaviour on validation failure: retry, fall back, or escalate | A detector with no decision attached, which is a log line |

## 6. The escalation ladder

Climb one rung at a time, and only with evidence that the rung below is
exhausted. Every rung costs more than the one under it.

1. Write the prompt better. Structure, explicit contract, absent case
   specified. Free and fixes more than students expect.
2. Show examples. Few-shot for boundaries and conventions. Input tokens on
   every call, forever.
3. Split the call. Chaining, routing, parallelising, when one prompt is
   carrying several jobs. Week 3.
4. Give it tools. When the information or the action is outside the model.
   Week 4.
5. Change the knowledge. Retrieval for facts you own, week 7. Fine-tuning is
   out of scope here, see AIE-Huyen chapter 7 if you are curious.

## 7. Things that are not true

- A longer prompt is a better prompt. Length is a cost, not a quality.
- A persona grants knowledge or permission. It changes register. Authorisation
  lives in your code, checked before the tool runs.
- A schema makes the content correct. It makes the shape correct.
- A prompt that reads better performs better. That is a hypothesis, and you
  own a harness.
- A prompt tuned on one model transfers to its successor. Re-run the
  evaluation on every model change.
- "think step by step" is still the state of the art. It was a 2022 finding
  about non-reasoning models and the landscape has moved.

## 8. The review habit, two minutes per prompt

1. Read the instruction and the examples together as one document, looking
   only for contradictions.
2. Ask what the prompt does for every case you did not mention. If you cannot
   answer, that case is unspecified, which means unpredictable.
3. Ask which line you could delete without changing a measured number. Delete
   it, measure, and keep the deletion if nothing moved.
4. Ask where the untrusted text is, and confirm it is delimited and that the
   system message says it is data.
