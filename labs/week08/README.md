# Week 8 practical: retries, recovery, and a human approval gate

BPINFOR-132, Designing, Verifying, and Shipping AI Agents.
Duration: 2 teaching units, 90 minutes. Bring a laptop.

## What your system gains this week

Increment eight. Everything you have built so far assumes its dependencies
answer. Today you find out what happens when they do not, and you put a
human in front of the one step you cannot undo.

## Why this session exists

The lecture said to choose one of retry, fallback, degrade, or escalate per
step in advance, by consequence, and to record which one fired. Today you
choose four of them, in code, and a fault harness makes each choice visible.

**No model is called in blocks 1 and 2.** The tools are offline and the
faults are deterministic, so blocks 1 and 2 run in about a second and
the same seed gives the same failures every time. That is deliberate: this
session is about what your code does when a dependency misbehaves, and a
real model in the way would add a second source of failure you would then
have to rule out.

## Learning outcomes exercised

Outcome 7 (a working application), outcome 9 (verifying behavior under
adversarial conditions), outcome 12 (trade-offs).

## Before you arrive

Read ADP-Gulli chapters 11 to 13 and the monitoring sections of AIE-Huyen
chapter 10. Install the two new dependencies:

```bash
pip install langgraph langgraph-checkpoint-sqlite
```

This session also carries the mid-semester project check-in: ten minutes
per group, during the build blocks, formative and not graded. The sign-up
order is on Moodle. Bring your repository as it is, not slides and not a
demonstration, plus one written list: what is in your own application,
what is out, and what is still open. The weekly starters are standalone,
and wiring each one into your application in `app/` is your job. The one
question you will be asked is the one that matters for the rest of the
semester: in week 10 you will run this system many times with no human
present, so what currently prevents that. You leave with two or three
actions written down by you. This is the last cheap moment to change your
architecture.

## Timing

### This edition only, 2026/2027

The application skeleton arrived this week rather than in week 1, so the
session opens with a 20 minute integration block and everything after it is
shorter. Do the steps in `INTEGRATION.md` before you arrive, and install
LangGraph at home, because there is no setup time for it in the room.

| Time | Block | What you do |
| 0 to 20 | Integration | `app/` assembled, run end to end, ready for the check-in |
| 20 to 25 | Setup | Read `faults.py`, run the baseline once |
| 25 to 30 | Break it | Run the fault matrix with no policy. Record what dies. |
| 30 to 55 | Survive it | TODO 1 to 5: the ladder, validation, and a degrade path |
| 55 to 85 | Gate it | TODO 6 and 7: one gated step, resumed from a second process |
| 85 to 90 | Close | Commit, push, write today's four decisions |

The stretch moves to homework, where both of its options already are. The
side effect above the interrupt is demonstrated once on the projector, and
proving it on your own pipeline is homework too.

### The session as designed

| Time | Block | What you do |
| 0 to 8 | Setup | Install, read `faults.py`, run the baseline once |
| 8 to 15 | Break it | Run the fault matrix with no policy. Record what dies. |
| 15 to 45 | Survive it | TODO 1 to 5: the ladder, validation, and a degrade path |
| 45 to 78 | Gate it | TODO 6 and 7: one gated step, resumed from a second process |
| 78 to 85 | Stretch | The unanswered approval, or a trace |
| 85 to 90 | Close | Commit, push, write today's four decisions |

## The harness

Eight injectable faults: timeout, rate limit, server error, malformed,
empty, slow, contract drift, and flaky. Aimed from the command line, so no
test edits your pipeline:

```bash
python starter/01_survive.py --baseline             # no policy at all
python starter/01_survive.py                        # the full matrix
```

Deterministic by construction. Given a seed, a tool name, and a call index,
the same fault fires on the same call every time. A failure you cannot
reproduce is a failure you cannot claim to have fixed.

**Contract drift is the interesting one.** It returns a valid response with
a renamed field. No retry will ever fix it, because the call succeeded.

## Block 1, break it (7 minutes)

Run the matrix with `--baseline` and record what happens, before you fix
anything. Seven minutes of watching your own pipeline fail is the most
valuable part of the session and students want to skip it. A group that has
not seen the unhandled failure has nothing to compare their fix against.

## Block 2, survive it (30 minutes)

TODO 1 and 2 in `retry.py`, TODO 3 to 5 in `graph.py`.

Watch the metric, not just the total. The obvious question is "did it
answer", and it is a trap: it counts a confidently wrong answer as a
success, so it rewards the pipeline with no validation. The scorer here
reports four outcomes instead. **The column that matters is WRONG.**

On the reference run, hardening does not produce more correct answers. It
takes five outright failures down to one, by converting them into degraded
answers that say what is missing. That is what graceful degradation buys,
and it is not what people expect.

**Checkpoint 1.** The items in `checklist.md`.

## Block 3, gate it (33 minutes)

TODO 6 and 7. Gate **exactly one** step, chosen by consequence, and be able
to say why the others are not gated. Gating everything trains the approver
to click through.

Then run it as two separate invocations, and kill the first process in
between:

```bash
python starter/02_gate.py start
python starter/02_gate.py resume approve     # or reject, or edit
```

A pause that only survives inside one script is a session variable with
extra steps.

**The edit path is not optional.** In practice the approver's most common
response is neither approve nor reject, it is approve with one field
changed. A gate with no edit path throws away correct work and trains the
approver to approve rather than to correct.

**Checkpoint 2.** Be ready to demonstrate the resume from a second process.

## The thing that is not on any slide

The interrupted node re-executes from its first line on resume, so anything
above the `interrupt()` call happens twice. That much is in the lecture.

What is not: **the recorded state will not show you the duplicate.** The
first execution never returns, so its return value is discarded while
whatever it did to the outside world is not. Put a deliberate side effect
above the interrupt, run both processes, and then look for it in the state.
It appears once and it happened twice.

The failure mode is a case file written twice or an email sent twice, on a
run that looks clean afterwards. The rule that follows is narrow and
absolute: **above an interrupt, read only.**

`interrupt_smoke_test.py` demonstrates it.

## Wire it in

Copy `retry.py` and `faults.py` into `app/`, with `from faults import`
changed to `from .faults import`, and set one `StepPolicy` per step in
`app/pipeline.py` as your `DECISIONS.md` chose them. The gate is written
rather than copied: in `app/graph.py`, write
`request_approval(payload, unattended)` around your `submit` node, and when
`unattended` is true return the timeout default you decided today instead of
waiting, because week 10 runs the application with nobody present. Prove it
with `python -m app.run --route request "The badge reader at the town hall
is broken."` and then `python -m app.run --batch`, which must finish without
waiting for anyone. If you missed the session, keep the stub and record
that in `DECISIONS.md`.

## What goes into DECISIONS.md today

Four entries. Template in `starter/DECISIONS_week08_section.md`.

1. Which errors you classified as retryable, and the one you deliberately
   excluded.
2. Which step you gated, and why the others are not.
3. What your pipeline does with an empty result, and why that is a decision.
4. What an unanswered approval does after the timeout, and who that protects.

## Homework

- Implement the timeout on an unanswered approval and prove it fires.
- Wrap one run in OpenTelemetry spans and show a trace where a retry, a
  fallback, and the gate are all visible.
- `python -m project.verify` passing.

## If you finish early

- Write a test that asserts the gate fired, with no human present. The
  answer involves resuming the graph programmatically, and discovering that
  is worth more than another feature.
- Put a write above the interrupt and prove the duplicate to yourself.

## Reference solution

In `solution/`, published after the session. The written answer to TODO 7 is
at the bottom of `02_gate.py` and its second half is the part worth reading.
