# Week 8: LangGraph verified, and one sharper lesson than the deck states

Written 2026-08-10, during the practical-track redesign. Week 8 was probed
before being rebuilt, because its central demonstration depends on an API
that moves between versions.

Reproduce with `interrupt_smoke_test.py`, run as two separate invocations:

```bash
python interrupt_smoke_test.py start
python interrupt_smoke_test.py resume approve
```

## The demonstration works

Versions: `langgraph` 1.2.10, `langgraph-checkpoint` 4.2.0,
`langgraph-checkpoint-sqlite` 3.1.1. All the imports the session needs are
present: `StateGraph`, `START`, `END`, `interrupt`, `Command`, and
`SqliteSaver`.

Verified:

| claim | result |
| a run pauses at `interrupt()` | yes, `__interrupt__` is present in the returned state |
| the payload survives | yes, the action and the reason come back intact |
| `get_state` reports where it stopped | yes, `next` is `('submit',)` |
| a **second process** resumes it | yes, with `Command(resume=...)` against the same `thread_id` |
| the earlier node does not re-run | correct, `prepare` ran once |

So the session's exercise, kill the process between the two invocations and
resume from a new one, is real on this version.

## The lesson is sharper than the deck currently says

The deck warns that on resume the interrupted node re-executes from its
first line, so anything above the `interrupt()` call happens twice. That is
correct, and the probe confirms it: a print statement placed above the
interrupt fires in **both** processes.

What the deck does not say is the part that makes it dangerous:

**The state will not show you the duplicate.**

The side effect ran twice. The recorded state contains it once. That happens
because the first execution never returns, it raises to persist the
interrupt, so its return value is discarded while whatever it did to the
outside world is not. Measured: `side_effects` reads
`['prepared', 'WROTE_ABOVE_INTERRUPT', 'SUBMITTED']` with no duplicate,
after the write above the interrupt executed twice.

So the failure mode is not "the state gets messy". It is that a case file
was written twice, or an email sent twice, or a payment taken twice, and the
run looks clean afterwards. That is worth a slide of its own, and it is a
better argument for putting writes below the interrupt than the current
phrasing.

## What that means for the session design

The existing block 2 exercise is right and should be kept: gate exactly one
step, chosen by consequence, and prove the pause survives by resuming from a
second process.

Add one thing to it. Have students put a deliberate side effect above the
interrupt, run the two processes, and then check the recorded state for it.
Finding that the state is clean while the effect happened twice takes two
minutes and it is the most useful thing in the block.

## Not yet checked

The eight-fault injection harness, the retry and fallback ladder, and the
`durability` argument on `invoke`. The compile signature confirms
`checkpointer`, `cache`, `store`, `interrupt_before`, and `interrupt_after`
exist; the durability setting was not exercised.
