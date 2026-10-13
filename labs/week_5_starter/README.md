# Week 5 practical: a planner, an executor, and a second agent

BPINFOR-132, Designing, Verifying, and Shipping AI Agents.
Duration: 2 teaching units, 90 minutes. Bring a laptop.

## What your system gains this week

Increment five, and two changes at once.

The hand-rolled loop from week 4 gives way to **Pydantic AI**. Open your
week 4 `agent.py` next to this week's `agents.py`: the loop, the message
list, the tool dispatch, and the schema envelope are all gone. Nothing
underneath has changed, the framework makes the same calls to the same
endpoint in the same wire format, which is exactly why you wrote the loop
first.

And the agent gains a **planner** and a **reviewer**, so there are three
architectures to compare rather than one to admire.

## Why this session exists

The lecture put every multi-agent pattern on one axis, who decides the
control flow, and argued that a second agent is only worth it for tool
coordination or genuinely distinct expertise. Today you test that on your own
task, with a cost number attached, against a verifier that cannot be argued
with.

Coding is the domain for one reason: it is the only agentic task in this
course with a free, fast, deterministic verifier. The tests pass or they do
not. Every other domain has to build a judge, and that is weeks 10 to 12.

## Learning outcomes exercised

Outcome 2 (patterns and their trade-offs), outcome 6 (decomposing a problem
into an architecture), outcome 12 (justifying trade-offs).

## Before you arrive

Read ADP-Gulli chapters 6 and 7, and MAS-Dibia chapter 1 on when **not** to
use multi-agent. Install the one new dependency:

```bash
pip install "pydantic-ai-slim[openai]"
```

## Timing

| Time | Block | What you do |
| 0 to 10 | Setup | Install, run the test suite, read the failure and the four modules |
| 10 to 45 | Plan and fix | TODO 1 to 4: the plan schema, its validator, and the fix proposal |
| 45 to 70 | Second agent | TODO 5: the reviewer, and the three-way comparison |
| 70 to 85 | Measure | TODO 6 and 7: read the table, and the gold set |
| 85 to 90 | Close | Commit, push, write the numbers into `DECISIONS.md` |

## The task and the toy repository

A small booking-fee library for a commune sports hall: four modules, sixteen
tests, no dependencies. One test fails. The off-peak discount is meant to
apply from 20:00, and a booking starting at exactly 20:00 misses it.

The agent works on a **copy**. `Work.fresh()` makes one per run, so a
destructive agent costs you nothing. If you edit `toyrepo/` directly, your
next run starts from a repository that is already fixed and every number
after that is meaningless.

## The three architectures

| | what it can do |
| A baseline | free-form tool loop: list, read, replace any line, run tests |
| B planner | plan, validate the plan for free, then propose **one** line change |
| C planner + reviewer | the same, with a second agent gating the proposal |

One variable changes across them: how much architecture sits between the
model and the edit.

## Block 1, plan and fix (35 minutes)

TODO 1 to 4 in `agents.py`.

**TODO 1 carries a warning worth reading before you write it.** The obvious
plan schema is a list of nested `Step` objects. It does not work on this
model, and it does not fail gracefully: it raises
`Exceeded maximum output retries` every time. A flat list of strings
validates. Schema complexity is a cost you pay in reliability, and the right
schema is the shallowest one that carries what you need.

**TODO 3 is the design decision of the session.** The executor does not edit
the file. It proposes exactly one line change, and `repo.apply_fix` decides
whether to apply it, refusing anything that touches a test, names a line that
is not there, or is ambiguous. Note who enforces that: not the model, and not
its instructions.

**Checkpoint 1.** The six items in `checklist.md`.

## Block 2, the second agent (25 minutes)

TODO 5. The reviewer sees the diff and the test output, and **not** the
fixer's reasoning. If it inherits the reasoning it inherits the mistake, and
the second opinion stops being a second opinion.

Then run all three architectures and read the table.

**Checkpoint 2.** Be ready to say which architecture you would ship and what
the other two cost.

## Working with the recording

```bash
python starter/01_compare.py --replay
```

Week 5's recording is different from weeks 1 to 4. Those record model calls
and replay them. This one records the **outcome** of each whole pipeline,
three times per architecture, because the pipeline mutates a copy of a
repository and replaying calls into a changing file system would be a lie.

The baseline in the recording is slow and never succeeds. That is the
finding, not a defect.

## What goes into DECISIONS.md today

Six entries. Template in `starter/DECISIONS_week05_section.md`.

1. Your plan schema, and what happened when you tried a nested one.
2. Your validator: which checks, and what happens when one fails.
3. The three-way table: green out of three, tokens, and seconds each.
4. One sentence on **why** the baseline fails, that is not "the model is too
   small".
5. The reviewer's verdict on each run, and whether you would ship it.
6. What your verifier cannot catch. This is the most valuable line on the
   page and week 10 comes back for it.

## Homework

- Run all three live, three times each, and put your table next to the
  recorded one.
- Task B, the refactoring: the same discount rates are written out in four
  places and should become one. It has no single failing test to guide it,
  so the planner matters far more. Report whether the gap between
  architectures widens.
- `python -m project.verify` passing, gold set at 46 cases.

## If you finish early

- Hand the reviewer a deliberately bad patch: one that deletes the failing
  test instead of fixing the bug. `apply_fix` refuses it, so hand the
  reviewer the diff directly. Does it catch it? A reviewer that approves it
  has told you something the happy path never would.
- Make the fixer propose the wrong-but-passing fix on purpose, by telling it
  the constant is suspect. Then check whether your reviewer catches it and
  whether the test suite does. One of them should.

## Reference solution

In `solution/`, published after the session. The written answer to TODO 6 is
at the bottom of `01_compare.py`, and the second and third points in it are
the ones worth reading.
