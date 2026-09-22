# Week 2: a structured-output extractor, measured

Copy this into your `DECISIONS.md` and fill it in.

---

## Week 2

**Run conditions.** model: [ ] | temperature: 0.0 | prompt version: [ ] |
served locally | date: [YYYY-MM-DD] | scored on: [the recording / my own
machine]

### 1. The output contract

The conventions I chose, and why:

- due_date, when the message states no date: [ ]
- due_date, when the message states only a relative expression: [ ]
- quote, and what "verbatim" means in my scorer: [ ]
- what my scorer does with a record that failed validation: [ ]

[One sentence on why the last one matters. A scorer that skips the records
it could not parse reports a number that improves as the model gets worse.]

### 2. Zero-shot, per field

| field | correct | of |
| category | | 10 |
| urgency | | 10 |
| due_date | | 10 |
| quote | | 10 |
| invalid records | | 10 |

My prediction, written before block 3: examples will help most on [ ]
because [ ].

### 3. Few-shot

Examples chosen, and the job each one does:

| example | why it is in the block | field it should move |
| | | |
| | | |
| | | |

| field | zero-shot | few-shot | move |
| category | | | |
| urgency | | | |
| due_date | | | |
| quote | | | |

### 4. What got worse

[Name the field, if any, and diagnose it. If nothing got worse, say so and
say how you checked. Then look at the failure lines rather than the counts,
and say whether any error disappeared or merely changed shape. A wrong label
that became a different wrong label has not been fixed.]

### 5. What the examples cost

- extra input tokens per call: [ ]
- per thousand calls: [ ]
- estimated euros per thousand calls on the small tier: [ ], against the
  price list dated [ ]. Estimate, not a measurement.

### 6. Ship it or not

[Which variant, on what evidence, and what would change your mind. Ten
records is not enough to be confident and saying so is worth more than
claiming a win. If your answer is "keep one example and drop the rest", say
which one and why.]

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

### Deferred

[Anything you did not get to, and why.]
