# Week 8: retries, recovery, and a human approval gate

Copy this into your `DECISIONS.md` and fill it in.

---

## Week 8

**Run conditions.** fault seed: [ ] | attempts: [ ] | base delay: [ ] |
max elapsed: [ ] | LangGraph [version] | date: [YYYY-MM-DD]

### 1. Which errors are retryable

Retryable: [ ]

Deliberately NOT retryable: [ ], because [ ].

[The one that matters is contract drift. Say in one sentence why retrying a
call that succeeded is worse than useless.]

### 2. The fault matrix

| | correct | WRONG | degraded | failed |
| baseline | | | | |
| hardened | | | | |

What hardening actually bought:

[If your answer is "more correct answers", look at the table again. Count
the failed column before and after.]

### 3. The empty result

An empty result is not an error. My pipeline treats it as [ ], because [ ].

### 4. The gate

Gated step: [ ]. The others are not gated because [ ].

An unanswered approval after the timeout: [ ]. That protects [ ].

The approval payload carries [ ] and deliberately does not carry [ ].

### 5. The duplicate the state does not show

I put a side effect above the interrupt. It executed [ ] times. The recorded
state showed it [ ] times.

What that means for anything my gated node does before it asks:

[...]

### Deferred

[Anything you did not get to, and why.]
