# Decisions

## Week 1

**Run conditions.** Everything below was produced on:

- machine: [Apple, M4, 16GB]
- model: [qwen3-vl:4b, qwen2.5:7b, nomic-embed-text:latest, qwen3:4b-instruct]
- served by: Ollama, one request at a time, locally
- date: [2026-09-16]

Every number in this file is meaningless without those four lines, so they
are stated once here and referred to rather than repeated.

### 1. Machine and model set

I am running the qwen3-vl:4b, qwen2.5:7b, nomic-embed-text:latest, qwen3:4b-instruct model set.

[If you could not run the optional models, say so and say what you will do
before week 9. This is a constraint on your project, not a failure, and
naming it now is worth more than discovering it in week 9.]

### 2. The first call

| | |
| finish reason | stop |
| prompt tokens | 24 |
| completion tokens | 45 |
| elapsed | 1.5517885000444949 |

One sentence on the finish reason: what my program would do differently if
it came back as a truncation rather than a normal stop:
If the answer was cut off mid-sentence, my program should either retry the call with a higher max_tokens, rather than sending it as a finished answer to the user.

### 3. Variance

| cell | distinct (recording) | distinct (mine) | median latency |
| closed_short, t=0.0 | 1/12 | 1/6 | 0.175 |
| closed_short, t=1.0 | 1/12 | 1/6 | 0.175 |
| open_list, t=0.0 | 1/12 | 1/6 | 1.098 |
| open_list, t=1.0 | 11/12 | 6/6 | 1.138 |

Which cell still returns a single answer at temperature 1.0, and why that
one: 
The cell that returns a single anwser at temp = 1.0 is `closed_short`. This is because we limited the anwser of the question to 1 word, meaning for specific question there is only one possible anwser of one word. 

Which cells a test asserting exact string equality would pass on, and what
that tells me about testing this system:
The cells that would pass the test are: both of the `closed_short` at both temp (closed question even with high temp stays the same) and `open_list` at t = 0.0 (open question produces 1 identical anwser with t=0, since greedy decoding is deterministic). It will only fail on `open_list` at t = 1.0. So it passes at every run that produced idendical string, and fails when we have distinct > 1. 

The test doesn't test the model, it tests promt design and decoding settings. A test that passes today in the env, can fail in future when temp is adjusted for real use .

**The sentence that carries into week 10.** [One sentence about when you can
and cannot rely on repeating an output. Week 10 will ask you to find this
again. It should not say "the model is random", because your own table shows
otherwise in most cells.]

### 4. The cold start

- cold call: 2.567 s
- warm call: 0.101 s
- ratio: 25.7

What this implies for a system that uses more than one model, and what I
will do about it:

Loading a new model costs a lot so we have to be mindful of how to use multiple models, when is it worth it to load them? We can't just switch between them indefinitely. We will make sure to ask as many questions we can to one model before switching to the next one.

### 5. Cost, estimated

A 200-case golden set, at the token cost of my long case:

| | one run | nightly for the semester |
| small tier | 0.000168 EUR | 3.28 EUR |
| large tier | 0.012456 EUR | 244.14 EUR |

Estimates against the price list dated [date in `project/prices.py`], not
measurements. Running locally, my actual monetary cost was zero.

Which tier I would run nightly, which I would run before a release, and why
not the same one for both:

I would run the small tier every night and the large tier right before release. I wouldn't run the large tier every day as it is too expensive but I need to run it before release as it will give more accurate results.

### Deferred

[Anything you did not get to, and why. An explicit deferral with a reason is
engineering. Silence is not, and the project rubric can tell the
difference.]

## Week 2

**Run conditions.** model: qwen3:4b-instruct | temperature: 0.0 | prompt version: week02-zero-shot-v1 |
served locally | date: 2026-09-22 | scored on: my own
machine

### 1. The output contract

The conventions I chose, and why:

- due_date, when the message states no date: return null or None
- due_date, when the message states only a relative expression: null
- quote, and what "verbatim" means in my scorer: the quote has to appear as an exact substring inside the original message
- what my scorer does with a record that failed validation: it counts it
  as invalid and marks every field wrong for that record instead of
  skipping it

[One sentence on why the last one matters. A scorer that skips the records
it could not parse reports a number that improves as the model gets worse.]

This matters because a scorer that skips the records it could not parse would report a number that gets better the worse the model performs, since the broke outputs simply disappear from the count.

### 2. Zero-shot, per field

| field | correct | of |
| category | 7 | 10 |
| urgency | 9 | 10 |
| due_date | 7 | 10 |
| quote | 9 | 10 |
| invalid records | 0 | 10 |

My prediction, written before block 3: examples will help most on due_date
because the model's main failure is inventing a plausible date instead of returning null, showing an exmaple of when returning null should fix it.

### 3. Few-shot

Examples chosen, and the job each one does:

| example | why it is in the block | field it should move |

| | | |
| | | |
| | | |

| field | zero-shot | few-shot | move |
| category | 7/10 | 5/10 | -2 |
| urgency | 9/10 | 9/10 | +0 |
| due_date | 7/10 | 7/10 | +0 |
| quote | 9/10 | 8/10 | -1 |

### 4. What got worse

[Name the field, if any, and diagnose it. If nothing got worse, say so and
say how you checked. Then look at the failure lines rather than the counts,
and say whether any error disappeared or merely changed shape. A wrong label
that became a different wrong label has not been fixed.]
Category got worse, from 7/10 to 5/10. Due_date did not move at all, so
my prediction was wrong: the examples did not fix the invented-date problem. Adding examples seems to have pushed the
model toward mislabeling more messages as "facilities" that should have
been something else. Quote also dropped slightly, from 9/10 to 8/10.

### 5. What the examples cost

- extra input tokens per call: 280
- per thousand calls: 280000
- estimated euros per thousand calls on the small tier: [ ], against the
  price list dated [ ]. Estimate, not a measurement.

### 6. Ship it or not

[Which variant, on what evidence, and what would change your mind. Ten
records is not enough to be confident and saying so is worth more than
claiming a win. If your answer is "keep one example and drop the rest", say
which one and why.]
We would ship zero-shot because few-shot made category and quote worse. It did not move due_date at alm, which is the field we were expecting it to fix. 

### Sensitivity variant

Variant assigned: [ ]. What I changed: [ ]. What moved: [ ].

[If nothing moved, say so. A knob that changes nothing measurable is a real
result, and it tells the room which knobs are worth arguing about.]

### The gold set

Ten cases written to `artifacts/goldset.json`, tagged by language.

One thing my scorer cannot currently detect:

[This is the most valuable line on the page. An example: "our scorer cannot
tell a correctly formatted date that is simply the wrong date from a
correctly extracted one, because it only compares strings."]

It cannot tell a correctly formatted date that is simply the wrong date apart from a date that was invented outright, because it only compares strings against the gold date.

### Deferred

[Anything you did not get to, and why.]
The sentitivity variant since we werent assigned a role during the practical.

## Week 3

**Run conditions.** classifier model: qwen2.5:7b | answering model: qwen2.5:7b |
temperature: 0.0 | served locally | date: [2026-09-29] | scored on: my own machine

### 1. The five route definitions

| route | definition, one sentence, in terms of what the help desk must do |
| request | The help desk must process an incoming application, form submission, or action request from a resident. |
| info | The help desk must look up and provide general facts, opening hours, fees, or procedural guidance from the handbook. |
| status | The help desk must check and report on the current processing state or progress of an existing request or file. |
| complaint | The help desk must log and acknowledge a formal issue, grievance, or report of faulty municipal infrastructure. |
| other | The help desk must handle or route queries that fall outside standard commune administrative topics. |

My convention for the four ambiguous queries:

[Two defensible conventions exist. Neither is discoverable from the data.
What matters is that yours was written down before you measured, not which
one you picked.]
The four ambiguous queries were assigned based on core action intent.
When a message both reports an unresolved problem and complains about handling, the gold route is complaint. 
When chasing a report without dissatisfaction, it is status. 
When asking procedural questions while reporting a fault, it is request.

Do my definitions match the ones in `queries.py`? yes

### 2. The policy layer

Before choosing a threshold, the confidence values I saw were: min 0.00, max 0.99, 2 distinct values across 24 queries.

- confidence floor: 0.7, because 0.7 correlated with misclassified ambigous queries
- evidence check: falls back to other if an invalid evidence span indicades bad response by classifier
- safe default: info, because that specialist handles general commune queries safely without triggering a side effect

How often each check fired: below_threshold 1, evidence_not_verbatim 1,
invalid_decision 0.

[If a check fired zero times, say what that tells you. A threshold that
never fires is either a very good classifier or a useless signal, and the
confidence distribution above tells you which.]

Redirected safely when the policy checks fired twice, intercepting low confidence predictions and non verbatim evidence spans.

### 3. Route accuracy

| route | correct | of |
| request | 3 | 7 |
| info | 4 | 5 |
| status | 4 | 4 |
| complaint | 4 | 4 |
| other | 0 | 4 |

Overall 15/24. Excluding the four ambiguous: 12/20.

Confusion pairs, with direction:

| gold | applied | count |
| | | |

The route carrying most of the error is other and request. The fix is a prompt adjustement, because if we restrain the distinction between requesting administrative action or reporting a complaint will result in  request/complaint classification errors.

### 4. What routing cost

- monolith: 14032 tokens over 24 queries
- router: 12062 tokens over 24 queries
- the classifying call alone: 7724 tokens, which is 64 per cent of the
  routed total

I predicted that share would be 25 before measuring it.

[If the share surprised you, say why. The classifier's prompt carries every
route definition on every call, and the specialists carry only their own.]

### 5. What routing bought

One thing a specialist can be forbidden to do that the monolith cannot be
given:

A specialist  can be completely restricted from calling external tools or accessing senstiitve personal data APIs that other routes require.
Would I ship the router: no. Evidence: Routing accuracy wasnt too high (15/24) and latency doubled from 46s to 82.3s while clqssification took 64% of tokens. What would change my mind: improving clasisfier definitions to 90+% accuracy and reduce latency.

### 6. Stretch variant

Variant assigned: [ ]. Result: [ ].

[For model routing: report both models on accuracy, evidence verbatim, the
confidence range, and resident memory. If the smaller model won, say so
plainly and say what you think that means.]

[For voting: report the split-vote count at each temperature. If nothing
ever disagreed, that is the result. Say what it cost and what it bought.]

### The gold set

`artifacts/goldset.json` now holds 34 cases: 10 from week 2 and 24 added
today, with the four ambiguous ones tagged.

### Deferred

[Anything you did not get to, and why.]
The stretch variant, we did not have time to do it and werent assigned a variant.

