# Assembling your application, before the week 8 check-in

BPINFOR-132, Designing, Verifying, and Shipping AI Agents.
For this edition only. Do it before your week 8 practical: Tuesday 3
November for Groupe BICS, Wednesday 4 November for Groupe BINFO.

## Why this exists

Seven practicals have given you seven working exercises in `labs/`. They
were standalone on purpose, so that a missed session never blocked the next
one. The cost is that nothing has yet made them one system, and in week 10
that system has to run many times with nobody present, because your
evaluation harness reads what it records.

`app_skeleton.zip` is the missing shape. It is an application that runs end
to end today with every stage stubbed, each stub keeping the signature of
the week that replaces it. Carrying weeks 2 to 7 into it means replacing
the stubs of six weeks, which is mostly copying files and changing a few
import lines, not designing anything new. The design decisions are the ones
your `DECISIONS.md` already records.

Budget about an hour at home. The week 8 section on Moodle opens early, on
Friday 30 October, so you have the weekend. The first 20 minutes of the
practical go through it again in the room, so come with whatever you
managed.

## Step 1, install the skeleton (10 minutes)

From the root of your project repository, with your venv active, and with
`app_skeleton.zip` downloaded from the week 8 section on Moodle into the
folder above it:

```bash
unzip ../app_skeleton.zip                 # app_skeleton/: README, app/, tests/
cp -r app_skeleton/app ./app
cp app_skeleton/pyproject.toml .          # replaces the week 1 file
pip install -e .
python -m app.run "My heating has been broken for three weeks."
python -m project.verify
```

The `pyproject.toml` you copied in week 1 installs only `project`. The new
one installs `project` and `app`, so replacing it and rerunning
`pip install -e .` is not optional. If you had added anything to the
`dependencies` line of your old file, copy it across first.

The run should end with `outcome refused`, a list of ten stages all marked
STUB, and a line saying the trace was appended to `artifacts/traces.jsonl`.
That is the correct result: every stub refuses honestly rather than
pretending. `python -m app.run --stages` shows the same list at any time.

## Step 2, carry weeks 2 to 7 into the stubs (40 minutes)

Always copy from your own completed `labs/weekNN/starter/`, never from a
`solution/` folder. Inside `app/` the files are one package, so every
import of a sibling file becomes relative: `from routes import` becomes
`from .routes import`, and `import handbook` becomes `from . import
handbook`. Each module's docstring in `app/` repeats exactly what to copy.
Run the check command after each week, not at the end.

**Week 2, extraction.** Copy `labs/week02/starter/extractor.py` over
`app/extractor.py`, then add one line at the end of the file naming the
prompt your `DECISIONS.md` chose: `SYSTEM = SYSTEM_ZERO_SHOT`, or your
few-shot prompt pasted in from `02_few_shot.py` and assigned to `SYSTEM`.
It has no sibling import to change.
Check: `python -m app.run --route request "The badge reader at the town
hall is broken."` The route is forced because the router comes next.

**Week 3, routing.** Copy `routes.py` and `router.py` from
`labs/week03/starter/` into `app/`, and in `router.py` change
`from routes import` to `from .routes import`. If your `DECISIONS.md`
chose the monolith instead, leave the router stubs, delete the `route`
stage from `STAGES` and from `_text` in `app/pipeline.py`, and write down
why. Check: `python -m app.run "My bin was not collected."`, which should now
show a route of its own choosing.

**Week 4, the tools and the loop.** Copy `agent.py`, `tools.py`, and
`handbook.py` from `labs/week04/starter/` into `app/`. In `agent.py`, change
`from handbook import` and both `from tools import` lines to relative
imports, and add `persist=False` to the `rec.finish(` call at the end of
`run_task`, because the application writes one trace per request itself. In
`tools.py`, change `import handbook` to `from . import handbook`. Check:
`python -m app.run --route info "Which form do I use to change the bank
details on my waste collection invoice?"`, with `qwen2.5:7b` pulled.

**Week 5, the planner and the reviewer.** This one is written, not copied,
because the week 5 agents worked on a toy repository. Open `app/agents.py`,
keep `Plan`, `validate_plan`, and `Verdict`, and write `make_plan` and
`review` with your week 5 planner and reviewer prompts, checking plan steps
against `tools.REGISTRY` instead of file names. If you chose the plain loop
in week 5, keep the three pass-throughs and delete all three `@stub` lines.
Check: the week 4 command again.

**Week 6, memory and the MCP boundary.** Copy `labs/week06/starter/memory.py`
over `app/memory.py` unchanged. Copy `mcp_server.py` into `app/` and change
`from memory import` to `from .memory import`. Check:
`python -m app.run --subject "A. Muller" "When is my bin collected?"`, and
`python -m app.mcp_server` should start your server.

**Week 7, retrieval.** Copy `chunking.py`, `corpus_loader.py`, and
`retrieval.py` from `labs/week07/starter/` into `app/`, change their
sibling imports to relative ones, and copy the corpus to the root of your
repository with `cp -r labs/week07/corpus corpus`. Then replace the body of
`MemoryStore.search(subject, query, k)` in `app/memory.py` with your
retriever, without touching its signature. A dense version is about eight
lines:

```python
    def search(self, subject: str, query: str, k: int = 3) -> list[str]:
        from .chunking import load_chunks
        from .retrieval import DenseIndex
        if not hasattr(MemoryStore, "_index"):
            MemoryStore._index = DenseIndex(load_chunks(600, 80), name="app")
        return [c.text for c in MemoryStore._index.search(query, k=k)]
```

Use the chunk size and retriever your `DECISIONS.md` chose, and decide
whether your week 6 facts for `subject` still come first. If you did not
wire week 6, also delete the `@stub` line above `search`. The first search
in each run builds the index: about a second when the embedding model is
already loaded, about 16 seconds from cold on the teaching machine. Check: the week 6 command again, whose
`memory.search` line should now end in `hits 3`.

## Step 3, prove it (5 minutes)

```bash
python -m app.run --stages
python -m app.run "Which form do I use to change the bank details on my waste collection invoice?"
python -m project.verify
git add app pyproject.toml DECISIONS.md   # and corpus, if you did week 7
git commit -m "Assemble the application"
```

`--stages` should list every stage from week 2 to week 6 as built (week 7
lives inside the week 6 memory stage) and the week 8 and 9 stages as stubs.
Weeks 8 and 9 go in the same way after their practicals, and their briefs
have a "Wire it in" section that says how.

## If you missed a week

Keep that week's stub, and write one line in `DECISIONS.md` saying which
stage is still a stub and why. The application still runs, and every trace
it writes lists the stub in `notes["stubbed"]`, so the gap is visible to
you, to your harness in week 10, and to whoever marks the project. Do not
copy a reference solution in to fill it. A stage you did not build is
better shown as a stub than presented as your work.

## What to bring to the check-in

Your repository as it is, the output of `python -m app.run --stages`, and
the written list the brief asks for: what is in your system, what is out,
and what is still open. The question you will be asked is what currently
stops this application running many times with nobody present. A stub
that refuses honestly is a fine answer for today. A stage that only exists
in `labs/` is the one to fix.

## The session, this edition

| Time | Block |
| 0 to 20 | Integration, this handout, in the room |
| 20 to 25 | Setup: read `faults.py`, run the baseline once |
| 25 to 30 | Break it: the fault matrix with no policy |
| 30 to 55 | Survive it: TODO 1 to 5 |
| 55 to 85 | Gate it: TODO 6 and 7, resumed from a second process |
| 85 to 90 | Close: commit, push, write today's four decisions |

Install LangGraph at home with
`pip install langgraph langgraph-checkpoint-sqlite`. There is no setup time
for it in the room.
