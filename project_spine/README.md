# The project spine

Course-provided code that every practical session reads or writes. You copy
it into your repository once, in week 1, and it stays there for fourteen
weeks.

This exists because of one promise the course makes: the practical sessions
are not fourteen exercises, they are one system built in fourteen
increments, and that system is the project that carries 40 per cent of your
grade. A promise like that is easy to make in a brief and hard to keep in
code. The spine is how it gets kept.

## What is in it

| File | What it is for | First used |
| `project/contracts.py` | The artifacts that cross week boundaries, as schemas | Week 1 |
| `project/trace.py` | Recording one run, and reading runs back | Week 1 |
| `project/models.py` | The local models, addressed by role rather than by name | Week 1 |
| `project/fixtures.py` | Replay fixtures, and the fallback when a handover is missing | Week 2 |
| `project/prices.py` | Hosted cost estimates, labeled as estimates | Week 1 |
| `project/verify.py` | `python -m project.verify`, run it before you commit | Week 1 |

It is about 1300 lines, roughly half of which is comment explaining why a
choice was made rather than what the line does. You are expected to read it.
Several sessions ask you to explain a decision taken in it, and week 12 asks
you to attack it.

## Installing it

In week 1, from the root of your project repository:

```bash
unzip project_spine.zip                 # from Moodle
cp -r project_spine/project ./project
cp project_spine/pyproject.toml .
pip install -e .                        # so any script can `import project`
python -m project.verify
```

The editable install is what lets `python labs/week01/starter/00_preflight.py`
find the spine: Python puts the script's own folder on the path, not the
folder you run from, so without it every script would have to guess where
`project/` is.

`verify` reporting that nothing is written yet is the correct result on day
one.

## The one artifact that matters most

`artifacts/traces.jsonl`. One line per run of your system, from week 4
onward, in the shape of `contracts.Trace`.

Week 10 builds the evaluation harness on it. Week 11 gates on it. Week 12
attacks the system that writes it. Week 13 cites it as evidence in a risk
assessment. If you keep exactly one thing tidy this semester, keep this.

The schema forces a habit the whole course is about. You cannot write a run
without `Conditions`, which means you cannot record a number without also
recording the model, the temperature, and the date that produced it. A
number without its conditions is not evidence, and here that is enforced by
the type rather than by a reminder on a slide.

## Two things the spine deliberately does not do

**It does not hide the model call.** Weeks 1 to 4 call the endpoint by hand
with the `openai` SDK, so you see the message list, the tool schema, and the
stop reason. From week 5 Pydantic AI makes the same calls. Nothing changes
underneath, which is the point of adopting a framework only after you have
written the loop yourself.

**It does not fill in your reasoning.** `load_or_reference` will hand you the
reference gold set when yours is missing, and it will print a line telling
you to record that you used it. That is a safety net for a missed session,
not a shortcut. A result computed on the reference pipeline is a result
about the reference pipeline.

## Running its tests

```bash
cd project_spine && python -m pytest tests -q
```

Seventeen tests, no network, no model, well under a second. They check that a
trace survives a round trip, that a replay fixture answers the call your
code actually makes and misses loudly when it does not, that the handover
fallback works and announces itself, and that the verifier catches a broken
artifact and names the field.

If you change `contracts.py`, run these first. They are the reason a
handover breaks in front of you rather than in week 10.
