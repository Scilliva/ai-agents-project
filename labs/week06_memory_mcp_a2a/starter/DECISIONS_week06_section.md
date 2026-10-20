# Week 6: memory, a stateless MCP server, and an A2A channel

Copy this into your `DECISIONS.md` and fill it in.

---

## Week 6

**Run conditions.** MCP SDK version: [ ] | specification revision:
2026-07-28 | model: [ ] | served locally | date: [YYYY-MM-DD]

### 1. The handle

Format I chose: [ ]

A guessable handle would expose: [ ]

### 2. Conflict and retention

- A write that contradicts an older fact: [keep both / overwrite], because [ ]
- How long a record lives: [ ], because [ ]

[Nothing expires by default. If you kept it that way, say so explicitly
rather than leaving it unsaid. An undeclared retention policy is still a
retention policy.]

### 3. What k costs

k = [ ]. Tokens added per call: [ ].

At four hundred facts in the store, this design [ ].

### 4. Memory off against memory on

| | tokens | turns to finish |
| memory off | | |
| memory on | | |

[The interesting result is usually that memory costs more tokens per call
and fewer calls per task. Whether that is a win depends on the task, and
saying which way it went for you is the entry.]

### 5. The protocol, at the wire

| server mode | status | Mcp-Session-Id | answered |
| stateless_http=True | | | |
| stateless_http=False | | | |

The error the session-mode server returned, quoted exactly:

[ ]

Why the two-server handle demonstration does not prove this on its own:

[ ]

### 6. What forget does not reach

[Deleting the fact does not un-say it: anything already copied into a
running conversation's messages is still there. Say what that means for a
resident who asks you to delete something.]

### Deferred

[Anything you did not get to, and why.]
