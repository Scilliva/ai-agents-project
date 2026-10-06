# Composing LLM calls: a one-page reference

Week 3, BPINFOR-132. After ADP-Gulli chapters 1 to 3. Keep this open while
you decide what to build, not after you have built it.

Every pattern here has three lines that matter: what it buys, what it costs,
and the new failure mode it introduces. A pattern proposed without all three
is a diagram, not a design.

## The question to ask, in order

1. **Have you measured it?** If not, go back to the week 2 harness.
   Architecture applied to an unmeasured failure is unfalsifiable.
2. **Is one prompt doing several jobs?** Then chain, and put a real check
   between the steps.
3. **Does the right handling depend on the input?** Then route, and measure
   the classifier separately from the answers.
4. **Are the parts independent?** Then fan out for latency, and give every
   branch a timeout.
5. **Is the variance the problem?** Then vote, if you can afford the
   multiplier and the answer has a majority.

If the sequence of steps itself depends on what the model discovers along the
way, none of these fit and you need a loop. That is week 4.

## Chaining

Several calls in a fixed order, with your code between them.

| | |
| Buys | One job per step, so a failure has one address. Per-step models, budgets, and evaluation. Inspectable intermediate state. |
| Costs | Latency adds up. Every step re-sends its own instructions, so total input tokens usually go up, not down. |
| New failure | Errors propagate downstream silently. Step three works perfectly on step two's wrong answer. |

**The gate is the design.** If there is nothing between two calls except
string concatenation, you have written one long prompt with extra latency. A
gate is ordinary Python: a schema check, a threshold, a lookup, an early
exit.

**Chaining does not multiply reliability.** Three steps at 0.95 each, with no
gate, is about 0.86 end to end. The reliability comes from the checks, because
a caught error is a retry or an escalation rather than a silent wrong answer.

**Early exit is a cost control.** A chain that stops after step one on a third
of its inputs has saved a third of its second-step budget. Read your own data
before you assume the fraction is small.

## Routing

Classify the input once against a closed set, then run the prompt built for
that class.

| | |
| Buys | Short specialised prompts instead of one hedging prompt. Per-route evaluation. Per-route model choice, which is where the money is. |
| Costs | An extra call on every request, including the trivial ones. Route definitions to maintain as traffic drifts. |
| New failure | The misroute: a good answer, well formed, produced by the wrong specialist. Every component behaved as specified. |

**Build the classifier as cheaply as it will go.** Rules first (free, instant,
brittle), then embeddings (cheap, needs labelled data), then a small model
call (handles paraphrase and multiple languages, costs a call every time),
then a trained classifier (best once you have your own logged traffic, and it
belongs to the machine learning course).

**A self-reported confidence is not a calibrated probability.** It is a number
the model generated. Use it as a relative ordering and threshold it on
labelled data. Do not do arithmetic with it.

**Five options when the router is uncertain**, each with a different price:
default route, overlap by design, reroute once with a cap, vote, escalate to a
human. A sixth is legitimate: accept the error rate on a route where being
wrong is cheap, and monitor it.

**Measure two things, per route, as counts.** Route accuracy against a
labelled set, and answer quality on the correctly routed cases. One combined
number hides the only failure mode routing introduces.

**Log the decision on every request.** Route, confidence, evidence, model,
tokens, latency. Without it a misroute is undiagnosable after the fact, and
you can never build the labelled set that would let you replace the model
call with something cheaper.

## Parallelisation

Independent calls issued at the same time, then combined. Two purposes, same
mechanism, entirely different justifications.

### Sectioning, for latency

| | |
| Buys | Wall clock becomes the slowest branch instead of the sum. Total tokens roughly unchanged. |
| Costs | Complexity: interleaved logs, partial failures, one branch that hangs. |
| New failure | The parts were not actually independent, and it fails quietly under load rather than in testing. |

Independence test: could you swap the order of the two calls without changing
the result? If not, they are not independent.

### Voting, for consensus

| | |
| Buys | Reduced variance on a task with a well defined majority. Disagreement as a free ambiguity signal. |
| Costs | The bill multiplies by the number of samples. |
| New failure | Agreement is not correctness. A model that misreads the task gives you five confident identical wrong answers. |

Voting works on small closed label sets where a majority is well defined. It
does not work on long free-text generation, where three drafts have no
natural majority and the combiner becomes another model call with its own
failure modes.

### The practical constraints

- Rate limits are per minute on requests and on tokens. A fan-out is the
  fastest way to meet both. Cap the pool deliberately, back off with jitter.
- Give every branch a timeout. Without one, a slow provider turns into a hung
  request and the latency argument collapses.
- Prompt caching and concurrency interact badly. As of August 2026 the major
  providers document that a cache entry becomes available only once the first
  response has begun, so branches launched together all miss the cache and
  pay full input price. Stagger the first request, or accept the cost.
- If nobody is waiting for the result, you do not need concurrency at all.
  Batch endpoints trade hours of latency for roughly half the price. An
  evaluation run is offline by definition, which is why week 10 uses them.

## The habits that apply to all three

Do:

- Give every step its own prompt module, version, and contract
- Put a deterministic check between steps, and decide what a failed check does
- Log the route, the confidence, the model, the tokens, and the latency
- Keep a monolith baseline running, so you can show what the composition bought
- Cap everything: steps, reroutes, votes, concurrency, calls per request

Do not:

- Split a prompt without saying which failure the split prevents
- Trust a self-reported confidence as if it were calibrated
- Report one overall accuracy for a routed system
- Fan out without a timeout, a concurrency cap, or a combiner that handles
  disagreement
- Add a pattern because the diagram looked thin

## One sentence per pattern, for the exam

- Chaining trades latency and cost for reliability, and only the gates
  deliver the reliability.
- Routing trades a classification risk for cheaper, better specialised
  handling, so measure the classifier separately.
- Parallelisation trades money for latency or for consensus, and consensus is
  agreement, not correctness.
