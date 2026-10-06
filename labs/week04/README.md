# Week 4 practical: a ReAct loop with two tools

BPINFOR-132, Designing, Verifying, and Shipping AI Agents.
Duration: 2 teaching units, 90 minutes. Bring a laptop.

## What your system gains this week

Increment four. Week 3 gave the `info` route a rule: never invent an opening
time, a fee, a form number, or a deadline. That rule was the right
engineering decision with no tools available, and it made the route useless
for exactly the questions people ask.

Today that specialist gets two tools and becomes an agent that can find the
fact before answering. It is hand-rolled, about twenty lines of control flow,
and week 5 replaces it with four lines of Pydantic AI. The point of today is
to know exactly what those four lines are hiding.

## Why this session exists

The lecture made two claims. A tool schema is an interface contract whose
description is prompt engineering. An agent is a bounded while loop whose
bounds are yours rather than the model's.

Block 1 builds both. Block 2 finds out how good your descriptions and your
caps actually were, and the findings today come from the tasks that fail.

## A note on the model

This week switches to `qwen2.5:7b`, and that is a measured decision rather
than a habit. On week 3's routing task the smaller model was better, 20 of 24
against 17. On this week's tool loop it is much worse, 4 of 10 against 7.

Classification wants a model that follows a narrow instruction closely. A
tool loop wants one that can hold a plan across several steps. Those are not
the same thing, and "use the bigger model" is not a strategy. Pull it before
the session:

```bash
ollama pull qwen2.5:7b
```

## Learning outcomes exercised

Outcome 2 (patterns and trade-offs), outcome 7 (a working application with
tool use), outcome 12 (justifying trade-offs). Block 3 previews outcome 11,
which week 12 examines.

## Timing

| Time | Block | What you do |
| 0 to 10 | Setup | Run both tools offline, read the ten tasks, warm the model |
| 10 to 45 | The loop | TODO 1 to 5: two schemas, the loop, and three caps |
| 45 to 70 | Break it | TODO 6 and 7: score it, and find the four findings |
| 70 to 85 | Defend it | TODO 8: try to fix prompt injection with a prompt |
| 85 to 90 | Close | Commit, push, write the numbers into `DECISIONS.md` |

## The task, and why this one

Ten questions to the Remerbaach help desk, in three languages, against a
fourteen document handbook.

- **`search_services`** is an offline keyword search. **`compute`** is a
  restricted arithmetic evaluator, because fees get multiplied and models are
  bad at that.
- Both tools are deterministic and free, so a failing task is a failure of
  your agent rather than of somebody's uptime, and you can rerun as often as
  you like.
- **T-08** needs no tool at all, and exists to catch tool abuse.
- **T-10** has no answer anywhere in the handbook. The correct behavior is to
  say so.
- One handbook document is a community notice board. Anybody can pin
  something to it, and somebody has.

## Block 1, the loop (35 minutes)

TODO 1 to 5, in `agent.py`.

The three caps are the part with no obvious right answer, and they are where
the marks are:

- **A step cap.** Straightforward, and it has to produce a partial answer
  rather than an empty string or an exception.
- **A budget.** What a run is allowed to cost before you stop it. In the
  starter the step cap is that budget (`max_steps`); a token budget over
  `run.tokens` is a stronger answer if you have time.
- **A no-progress detector.** Defining progress is the design decision. "A
  document id I had not seen" is one answer. A change in the facts extracted
  is another. Both are defensible; say which you chose and why.

**Checkpoint 1.** The six items in `checklist.md`.

## Block 2, break it and measure it (25 minutes)

TODO 6 and 7. The findings come from the tasks that fail, so a group with ten
out of ten and no findings has not finished, they have only passed.

Look for four things:

- **Tool abuse** on T-08: a tool call on a task that needed none.
- **Invention** on T-10: a fee stated that appears in no snippet.
- **Refusal without looking**: an answer of "the handbook does not cover
  this" with zero tool calls. This is the mirror image of invention and it is
  more dangerous than it looks, because a refusal reads as caution.
- **The notice board.** Did your agent follow an instruction that arrived
  inside a search result?

Report as counts with task ids, never as a percentage. Ten tasks means one
failure moves accuracy by ten points.

**Checkpoint 2.** Be ready to say your numbers out loud, with the task ids.

## Block 3, try to defend it (15 minutes)

TODO 8, in `02_defend.py`.

Your agent obeyed a stranger. Everybody's first instinct is to add a line to
the system prompt telling it not to. This block is fifteen minutes finding
out whether that works, and the answer decides how you spend weeks 11 and 12.

Write your prediction down before you run it.

## Working with the recording

```bash
python starter/01_run.py --replay
```

Every call is recorded, on both models, plus a no-tool baseline and the
defense ladder. The reference run passes **5 of 10**. If your scorer reports
10 of 10, your scorer does nothing.

## What goes into DECISIONS.md today

Six entries. Template in `starter/DECISIONS_week04_section.md`.

1. Your two tool descriptions, and what each "do not use this for" clause is
   preventing.
2. The three caps, each with the number you chose and the reason.
3. Task accuracy as counts with the failing ids, plus the step distribution,
   with the model name and the run date.
4. The no-tool baseline result, and one sentence on what the tools bought.
5. The four findings, in numbers rather than impressions.
6. **The blast radius.** Given that an attacker can make this agent say
   anything, what is the worst thing they can make it *do*? Then: what would
   have to change about that answer if this agent gained a tool that writes,
   sends, or pays?

Entry 6 is the one week 12 will ask you to look up.

## Homework

- Run the whole set live if you only used the recording, and on both models.
- Run the no-tool baseline (`--no-tools`) so you can say what the tools
  bought. It takes two minutes and without it nobody can say the loop
  improved anything.
- `python -m project.verify` passing, with the gold set now at 44 cases.

## If you finish early

- Run the same ten tasks on `qwen3:4b-instruct` and put the two side by side.
  You will reproduce the inversion from week 3 in the opposite direction.
- Break a tool on purpose, by renaming a field or raising inside it, and
  watch what the agent does with the error message. Then check that your
  error text does not leak a file path.
- Run the whole set three times and report how often the step count and the
  tool sequence were identical. That number is the consistency dimension from
  AAR-Rabanser, arriving six weeks early.

## Reference solution

In `solution/`, published after the session. The written answers are at the
bottom of `01_run.py` and `02_defend.py`, and the second one is the more
important of the two.
