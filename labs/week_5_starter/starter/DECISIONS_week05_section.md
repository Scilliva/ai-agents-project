# Week 5: a planner, an executor, and a second agent

Copy this into your `DECISIONS.md` and fill it in.

---

## Week 5

**Run conditions.** model: [ ] | framework: Pydantic AI [version] |
runs per architecture: [ ] | served locally | date: [YYYY-MM-DD] |
table from: [the recording / my own runs]

### 1. The plan schema

What I tried first, and what happened:

[If you tried a nested list of Step objects, say what the error was. It does
not fail gracefully and the error message does not mention schemas.]

What I shipped, and why it is shaped that way:

[...]

### 2. The validator

| check | what it catches |
| | |
| | |
| | |

On a failed check my system [repairs once / refuses], because [ ].

### 3. The three-way table

| architecture | green | tokens (mean) | seconds (mean) |
| A baseline | /3 | | |
| B planner | /3 | | |
| C planner + reviewer | /3 | | |

### 4. Why the baseline fails

[Not "the model is too small". Look at what changed between A and B: it is
not the model and it is not the prompt. Name it.]

### 5. The reviewer

Verdicts across my runs: [ ] approve, [ ] reject.

Would I ship it: [ ]. Extra cost: [ ] tokens, [ ] seconds per run.

The case where it would earn its cost:

[...]

### 6. What my verifier cannot catch

[The most valuable line on this page. The test suite is free, fast, and
deterministic, and it still only checks the cases somebody wrote a test for.
Name a change that would make the suite green and still be wrong. Week 10
comes back for this.]

### Deferred

[Anything you did not get to, and why.]
