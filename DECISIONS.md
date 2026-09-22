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
