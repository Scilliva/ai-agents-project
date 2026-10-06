# Week 3: a router in front of the extractor

Copy this into your `DECISIONS.md` and fill it in.

---

## Week 3

**Run conditions.** classifier model: [ ] | answering model: [ ] |
temperature: 0.0 | served locally | date: [YYYY-MM-DD] | scored on: [the
recording / my own machine]

### 1. The five route definitions

| route | definition, one sentence, in terms of what the help desk must do |
| request | |
| info | |
| status | |
| complaint | |
| other | |

My convention for the four ambiguous queries:

[Two defensible conventions exist. Neither is discoverable from the data.
What matters is that yours was written down before you measured, not which
one you picked.]

Do my definitions match the ones in `queries.py`? [yes / no, and if no, what
that does to my accuracy number]

### 2. The policy layer

Before choosing a threshold, the confidence values I saw were: min [ ],
max [ ], [ ] distinct values across 24 queries.

- confidence floor: [ ], because [ ]
- evidence check: [what I do when the span is not in the message], because [ ]
- safe default: [ ], because that specialist [ ]

How often each check fired: below_threshold [ ], evidence_not_verbatim [ ],
invalid_decision [ ].

[If a check fired zero times, say what that tells you. A threshold that
never fires is either a very good classifier or a useless signal, and the
confidence distribution above tells you which.]

### 3. Route accuracy

| route | correct | of |
| request | | |
| info | | |
| status | | |
| complaint | | |
| other | | |

Overall [ ]/24. Excluding the four ambiguous: [ ]/20.

Confusion pairs, with direction:

| gold | applied | count |
| | | |

The route carrying most of the error is [ ]. The fix is [a definition / a
prompt / a bigger model], because [ ].

### 4. What routing cost

- monolith: [ ] tokens over 24 queries
- router: [ ] tokens over 24 queries
- the classifying call alone: [ ] tokens, which is [ ] per cent of the
  routed total

I predicted that share would be [ ] before measuring it.

[If the share surprised you, say why. The classifier's prompt carries every
route definition on every call, and the specialists carry only their own.]

### 5. What routing bought

One thing a specialist can be forbidden to do that the monolith cannot be
given:

[...]

Would I ship the router: [ ]. Evidence: [ ]. What would change my mind: [ ].

### 6. Stretch variant

Variant assigned: [ ]. Result: [ ].

[For model routing: report both models on accuracy, evidence verbatim, the
confidence range, and resident memory. If the smaller model won, say so
plainly and say what you think that means.]

[For voting: report the split-vote count at each temperature. If nothing
ever disagreed, that is the result. Say what it cost and what it bought.]

### The gold set

`artifacts/goldset.json` now holds [ ] cases: 10 from week 2 and 24 added
today, with the four ambiguous ones tagged.

### Deferred

[Anything you did not get to, and why.]
