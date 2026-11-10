# The application skeleton

Course-provided code that becomes your own the moment you unpack it. It is
the shape of the application your weekly increments go into, and it runs
end to end on day one with every stage stubbed.

The spine (`project/`) gives every week the same contracts. The skeleton
(`app/`) gives every week the same place to land, with a stub for every
increment. Without it, each practical
leaves you with one more exercise in `labs/` and no system, and week 10 asks
for a system that runs with nobody present. With it, each week's job is to
replace one stub, keeping its signature, rather than to invent an
architecture.

## Installing it

From the root of your project repository, next to `project/`, `labs/`,
`artifacts/`, and `DECISIONS.md`:

```bash
unzip ../app_skeleton.zip               # from Moodle: app_skeleton/
cp -r app_skeleton/app ./app
cp app_skeleton/pyproject.toml .        # declares both project and app
pip install -e .
python -m app.run "My heating has been broken for three weeks."
python -m project.verify
```

The archive carries the spine's current `pyproject.toml`, which installs
both `project` and `app`. On day one the run refuses politely, names every
stage that is still a stub, and appends one trace to
`artifacts/traces.jsonl`. That is the correct result.

## What replaces what

Each stub keeps the signature of the week that replaces it, taken from that
week's starter, plus the few names the pipeline needs that the starter does
not have, which the table marks as added. Copy your week's file over the stub, and change its sibling
imports to relative ones (`from routes import` becomes `from .routes
import`), because inside `app/` the files are a package. Each module's
docstring says exactly what to copy and which names `pipeline.py` calls.

| Stage | Module | Signature it keeps | Week |
| extraction | `extractor.py` | `ServiceRequest`, `SYSTEM` (added: one line naming your chosen prompt), `extract(client, system, document_text, model) -> (ServiceRequest or None, meta)` | 2 |
| routing | `routes.py`, `router.py` | `ROUTES`, `SPECIALISTS`, `classify(client, text, model, temperature) -> (Decision or None, meta)`, `apply_policy(decision, text) -> Routed`, `respond(client, system, text, model) -> (str, meta)` | 3 |
| tools and the loop | `tools.py`, `agent.py` | `SCHEMAS`, `search_services`, `compute`, `Run`, `run_task(client, task, model, max_steps, stall_limit, system, week) -> Run` | 4 |
| planner and reviewer | `agents.py` | `Plan(goal, steps)` (week 5's without `suspect_file`), `validate_plan(plan) -> (ok, problems)`, `Verdict`, and added: `make_plan(question) -> Plan`, `review(question, answer, evidence) -> Verdict or None`, `MODEL_NAME` | 5 |
| memory | `memory.py` | `MemoryStore.load(path)`, `MemoryStore.search(subject, query, k) -> list[str]` | 6 |
| the MCP boundary | `mcp_server.py` | `remember`, `recall`, `forget`, `open_case`, `case_subject` | 6 |
| retrieval | the body of `MemoryStore.search` | the same `search`, unchanged (delete its `@stub` line if week 6 was never wired) | 7 |
| retries and degrade | `retry.py` | `StepPolicy`, `StepResult`, `is_retryable(exc)`, `call_with_policy(fn, *args, policy, fallback, validate)` | 8 |
| the approval gate | `graph.py` | added: `request_approval(payload, unattended) -> {"verdict", "by", "arguments"}`, in week 8's payload and resume shapes | 8 |
| vision | `vision.py` | `VisionResult`, `read_group(image_path, group, fields, ...)` | 9 |
| checks and triage | `checks.py` | `GROUPS`, `CheckReport`, `run_checks(fields)`, `code_triage(fields, report)` | 9 |

Two stages are written rather than copied, because their week used a toy
domain: week 5's planner worked on a code repository and week 8's graph on
two toy tools. Their docstrings say what to keep from the week.

## How a stub stays honest

A stub does one of three things: it passes its input through, it refuses
and says so, or it falls back to the reference copy and says so. It never
pretends. Each stub function carries a marker, and when you copy your own
file over it the marker disappears with it. Every trace lists the stages
that are still stubs in `notes["stubbed"]`, and every step says whether it
ran a stub, so a stubbed stage cannot be presented as a built one.

If you missed a session, keep that week's stub and say so in
`DECISIONS.md`. The application still runs, and the trace records the gap.

## Running it

```bash
python -m app.run "<request>"               # one request, one trace
python -m app.run --stages                  # which stages are still stubs
python -m app.run --route request "<req>"   # skip the router, test one path
python -m app.run --batch --repeat 2        # the gold set, unattended, twice
```

The batch mode is what week 10 needs: every gold case, run more than once
under the same conditions, with no step waiting for a person. It reads your
own `artifacts/goldset.json`, or the reference copy from the newest of weeks
3 to 8 you have unpacked, and says which.

## Its tests

```bash
cd app_skeleton && python -m pytest tests -q
```

No network and no model, like the spine's. They check that every module
imports, that every stage starts as a stub, that an all-stub request writes
one valid trace, and that a batch run writes what the week 10 harness reads.
