# Week 4: a ReAct loop with two tools

Copy this into your `DECISIONS.md` and fill it in.

---

## Week 4

**Run conditions.** agent model: [ ] | temperature: 0.0 | step cap: [ ] |
budget: [ ] | stall limit: [ ] | served locally | date: [YYYY-MM-DD] |
scored on: [the recording / my own machine]

### 1. The two tool descriptions

| tool | what its "do not use this for" clause prevents |
| search_services | |
| compute | |

### 2. The three caps

| cap | value | why that value |
| steps | | |
| budget | | |
| no progress | | |

My definition of progress is [ ], and it does **not** fire when [ ].

### 3. Task accuracy

[ ]/10 passed. Failed: [ids].

Steps: min [ ], max [ ], mean [ ]. Caps fired: [ ].

### 4. What the tools bought

No-tool baseline: [ ]/10. With tools: [ ]/10.

One sentence on what the tools bought, and at what cost per task:

[...]

### 5. The four findings

| finding | result |
| tool abuse on T-08 | |
| invention on T-10 | |
| refusal with zero tool calls | |
| notice board: text reached the model | |
| notice board: agent followed it | |

[Quote the invented answer if there was one. An invented figure with an
invented citation is worse than one without, and it is worth having the exact
words in front of you when you write entry 6.]

### 6. Blast radius

Prompt-level defenses tried: [ ] of 8 blocked the injection.

Given that an attacker **can** make this agent say anything, the worst thing
they can make it **do** is:

[...]

That answer depends on the fact that this agent's only tools are a read-only
search and a calculator. It changes the moment the agent gains a tool that
writes, sends, or pays, because [ ].

What I would build first to bound that, and the week I expect to build it in:

[...]

[Week 12 will ask you to find this entry. Writing down a vulnerability you
have found and not yet fixed, with the week you expect to fix it, is exactly
what a security backlog is.]

### Deferred

[Anything you did not get to, and why.]
