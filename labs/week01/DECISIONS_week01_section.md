# Week 1: the stack, the first call, and what it costs

Copy this into your `DECISIONS.md` and fill it in. Keep the headings. In
week 13 this becomes a section of your project report that you do not have
to write.

---

## Week 1

**Run conditions.** Everything below was produced on:

- machine: [make, chip, RAM]
- model: [the model name, exactly as `ollama list` prints it]
- served by: Ollama, one request at a time, locally
- date: [YYYY-MM-DD]

Every number in this file is meaningless without those four lines, so they
are stated once here and referred to rather than repeated.

### 1. Machine and model set

I am running the [required / required plus optional] model set.

[If you could not run the optional models, say so and say what you will do
before week 9. This is a constraint on your project, not a failure, and
naming it now is worth more than discovering it in week 9.]

### 2. The first call

| | |
| finish reason | |
| prompt tokens | |
| completion tokens | |
| elapsed | |

One sentence on the finish reason: what my program would do differently if
it came back as a truncation rather than a normal stop.

[...]

### 3. Variance

| cell | distinct (recording) | distinct (mine) | median latency |
| closed_short, t=0.0 | 1/12 | | |
| closed_short, t=1.0 | 1/12 | | |
| open_list, t=0.0 | 1/12 | | |
| open_list, t=1.0 | 11/12 | | |

Which cell still returns a single answer at temperature 1.0, and why that
one:

[...]

Which cells a test asserting exact string equality would pass on, and what
that tells me about testing this system:

[...]

**The sentence that carries into week 10.** [One sentence about when you can
and cannot rely on repeating an output. Week 10 will ask you to find this
again. It should not say "the model is random", because your own table shows
otherwise in most cells.]

### 4. The cold start

- cold call: [ ] s
- warm call: [ ] s
- ratio: [ ]

What this implies for a system that uses more than one model, and what I
will do about it:

[...]

### 5. Cost, estimated

A 200-case golden set, at the token cost of my long case:

| | one run | nightly for the semester |
| small tier | | |
| large tier | | |

Estimates against the price list dated [date in `project/prices.py`], not
measurements. Running locally, my actual monetary cost was zero.

Which tier I would run nightly, which I would run before a release, and why
not the same one for both:

[...]

### Deferred

[Anything you did not get to, and why. An explicit deferral with a reason is
engineering. Silence is not, and the project rubric can tell the
difference.]
