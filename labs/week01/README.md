# Week 1 practical: the stack, the first call, and what it costs

BPINFOR-132, Designing, Verifying, and Shipping AI Agents.
Duration: 2 teaching units, 90 minutes. Bring a laptop.

## Why this session exists

Everything you build this semester sits on top of a service that generates
text one token at a time. Today you install it, make it answer, and measure
three things about the answer that most people never look at: how long it
took, what it would cost if you were paying, and whether it comes back the
same twice.

The third measurement is the one the rest of the course is built on, and the
answer is more interesting than you expect. It is not "yes" and it is not
"no". It is "it depends, and you have to measure which".

## What is different about this course

**Everything runs on your own machine.** There is no API key, no account, no
budget, and no bill. You will run a model that lives on your laptop, and
when you want to run an experiment two hundred times you can, without asking
anyone.

That has one honest consequence worth stating on day one. Running locally
removes the monetary cost, and monetary cost is a real engineering
constraint you will be graded on. So this course keeps it in view a
different way: you measure the costs that are real here, which are seconds
and gigabytes, and you estimate the euros from a dated price list. An
estimate labeled as an estimate is honest. An estimate presented as a
measurement is not, and week 13 has a word for that.

## Learning outcomes exercised

Outcome 1, the building blocks of a GenAI application. Outcome 12,
justifying trade-offs in cost, latency, reliability, and safety. This is
also increment one of the project.

## Before you arrive

1. Read AIE-Huyen chapter 1.
2. Install [Ollama](https://ollama.com) and pull the two required models.
   This is about 2.8 GB and it is much faster on your own network than on
   the room's.

```bash
ollama pull qwen3:4b-instruct
ollama pull nomic-embed-text
```

3. Set the context window, which is the most important setting on your
   machine and the one nobody thinks to change.

```bash
launchctl setenv OLLAMA_CONTEXT_LENGTH 8192    # macOS app, then restart it
# OLLAMA_CONTEXT_LENGTH=8192 ollama serve      # macOS or Linux, run it yourself
# setx OLLAMA_CONTEXT_LENGTH 8192              # Windows, then restart Ollama
```

Left unset, Ollama reserves memory for the model's maximum context, and two
of the course models advertise 262144 tokens. Measured on the teaching
machine, for a model that never sees more than about four thousand tokens
all semester:

| setting | reserved | where it runs | cold start |
| default, 262144 | 42 GB | 77 per cent on the CPU | 20.7 s |
| `OLLAMA_CONTEXT_LENGTH=8192` | 3.9 GB | entirely on the GPU | 3.5 s |

Eleven times the memory for context you will never use. On a 16 GB machine
it only makes things slow. On an 8 GB machine it is the difference between
this course working and not working. `00_preflight.py` checks it for you and
prints the fix.

If you did not manage any of this, come anyway. Block 1 starts the download
and block 3 runs against a shipped recording that needs no model at all.

## Timing

| Time | Block | What you do |
| 0 to 15 | Setup | Repository, the project spine, `00_preflight.py` green |
| 15 to 45 | First call | `01_first_call.py`: one call, four numbers, one trace |
| 45 to 70 | Variance | `02_variance.py`: the recording, then your own machine |
| 70 to 85 | Cost | `03_cost.py`: seconds, memory, and a euro estimate |
| 85 to 90 | Close | Commit, push, write `DECISIONS.md` |

Blocks 2 and 3 end in a checkpoint where two or three groups report their
numbers to the room. Reporting earns participation credit toward the 2 bonus
points.

## Block 1, setup (15 minutes)

Create the repository you will use for fourteen weeks. Download
`project_spine.zip` and `week01_starter.zip` from Moodle into the folder
where you will create it, then:

```bash
git init ai-agents-project && cd ai-agents-project
unzip ../project_spine.zip                        # project_spine/: README, project/, tests/
cp -r project_spine/project ./project             # the spine
cp project_spine/pyproject.toml .                 # so every script can import it
mkdir -p labs && unzip ../week01_starter.zip -d labs   # labs/week01/

python3 -m venv .venv && source .venv/bin/activate
pip install -e . -r labs/week01/starter/requirements.txt
echo "# Decisions" > DECISIONS.md

python labs/week01/starter/00_preflight.py
```

The starter archive is the **whole** lab folder, including its `fixtures/`
directory. Block 3 reads a recording from it. Every later week ships the
same way: `unzip ../weekNN_starter.zip -d labs` gives you `labs/weekNN/`,
and the reference solution arrives after the session as
`weekNN_solution.zip`, which unpacks on top of it as `labs/weekNN/solution/`.

Push the repository to a remote before you leave today. GitHub or GitLab,
private or public, the choice is yours, with one condition: the teaching
team must have access to it, read access is enough, from the moment your
group registers in week 3 until the grades are published. The group
registration on Moodle asks for the URL. A group shares one repository;
if you work alone, it is yours. Everything you are graded on is read from
this remote, so a commit that never got pushed does not exist.

If a model is still downloading, leave it running and skip to block 3, which
needs no model. Fix the environment with a person standing next to you
rather than at midnight.

### What the repository holds, and why

- `project/` is course-provided and shared by every week. Read
  `project_spine/README.md` once. You are expected to know what is in it.
- `artifacts/` is what your system writes. From week 4 onward every run
  appends to `artifacts/traces.jsonl`, and week 10 builds the evaluation
  harness on exactly that file.
- `labs/weekNN/` is that week's scratch work.
- `DECISIONS.md` is one line per decision with the reason. In week 13 it
  becomes a section of your report that you do not have to write.

Run `python -m project.verify` before every commit. Today it reports that
nothing is written yet, which is correct.

## Block 2, the first call (30 minutes)

Complete TODO 1 to 3 in `starter/01_first_call.py`.

A call that prints only the answer is not finished. Print, and be ready to
explain, all four of these:

1. the answer text
2. the finish reason, and how your program would tell a deliberate ending
   from a truncation
3. the prompt and completion token counts, and which of the two you control
4. the elapsed time, and which part of it a user would actually feel

Then close the trace. It writes one record to `artifacts/traces.jsonl` in the
shape every later week reads, and `python -m project.verify` confirms it.

**Checkpoint 1.** The six items in `checklist.md`.

## Block 3, does the model repeat itself (25 minutes)

Complete TODO 4 to 6 in `starter/02_variance.py`.

Start with the recording, because it costs nothing and puts the whole room
on the same numbers:

```bash
python labs/week01/starter/02_variance.py --replay --full
```

That is ninety-six real runs recorded on the teaching machine: four prompts,
two temperatures, twelve runs each. `make_fixture.py` is what produced it and
you can regenerate it yourself.

Then run your own two cells live and compare.

Three things to come out of this block able to say:

- what happened at temperature 0, and whether your machine agrees with the
  recording
- which cell still returns one single answer at temperature 1.0, and why
  that one. "The temperature did not work" is not the answer.
- which of these cells a unit test asserting exact string equality would
  pass on, and what that tells you about testing this system

**Checkpoint 2.** Be ready to read your numbers out loud, as counts.

## Block 4, what it costs (15 minutes)

Complete TODO 7 and 8 in `starter/03_cost.py`.

Two costs are measured and one is estimated.

- **Seconds.** A short answer against a long one, same model, same settings.
- **The cold start.** The number the recording deliberately leaves out, and
  the largest one you will see today. It decides something about week 3, so
  write down what.
- **Euros, estimated.** What a 200-case golden set would cost to run nightly
  for a semester, on a cheap tier and on an expensive one. Week 10 builds
  that golden set, so this is not a hypothetical.

## What goes into DECISIONS.md today

Five entries. The template is in `DECISIONS_week01_section.md`.

1. Your machine: model, RAM, and whether you are on the required or the
   optional model set.
2. The four numbers from your first call, with the model name and the date.
3. Your variance table, and the sentence from TODO 6 that carries into week
   10.
4. Your cold start measurement, and what it implies for a system that uses
   more than one model.
5. Your nightly evaluation estimate on both tiers, labeled as an estimate,
   and which tier you would run when.

## Homework

- Run the full sweep live on your own machine:
  `python labs/week01/starter/02_variance.py --full`. Eight cells rather
  than two. It takes a few minutes and it is the version of the table you
  put in `DECISIONS.md`.
- Pull the optional models before week 9:
  `ollama pull qwen2.5:7b` and `ollama pull qwen3-vl:4b`.
- Read `project_spine/README.md` and skim `project/contracts.py`. Week 4
  starts writing to that contract and it is easier if you have seen it.

## If you finish early

- Run the same sweep on `qwen2.5:7b` and put the two tables side by side.
  Does the larger model repeat itself more or less than the smaller one?
  Predict before you run it.
- Ask `00_preflight.py` a question it cannot currently answer: how much free
  memory does this machine have, and would the 7B model fit? Add the check.
- Take the twelve `open_list` answers at temperature 1.0 out of the
  recording and group them by meaning rather than by string. How many
  genuinely distinct answers are there? That number is what week 10 spends a
  session learning how to compute without you.

## Reference solution

In `solution/`, published after the session. The written answers to TODO 5
and 6 are at the bottom of `solution/02_variance.py` and they are the part
worth reading. Use it to check your reasoning, not to replace it.
