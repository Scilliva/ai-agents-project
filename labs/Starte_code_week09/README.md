# Week 9 practical: a vision step you can break on purpose

BPINFOR-132, Designing, Verifying, and Shipping AI Agents.
Duration: 2 teaching units, 90 minutes. Bring a laptop and last week's
repository.

## Where this fits

Week 7 gave your system retrieval and a way to score the retrieval half on
its own. Week 8 made it survivable: retries, graceful degradation, and a
human approval gate on the steps you cannot take back. Every input to your
system so far has been text you could read.

Today one input stops being text. The agent takes a document image, calls a
vision-language model, gets a structured object back, and then has to decide
whether it believes it. The approval gate you built last week is not
modified today. What is new is the predicate in front of it.

That predicate is the point of the session. When the input was text, a wrong
extraction could be caught by looking at the source, because the string was
either in the document or it was not. When the input is an image, checking
the extraction means looking at the image, and nobody looks at ten thousand
images. So today you build the checks that do not need a human to look, and
then you find out where they stop working.

## Why this session exists

Two reasons, and the second is the one that shows up in the project mark.

The first is that document understanding is the multimodal use case that
pays for itself today, in exactly the sort of administrative workflow the
fictional commune of Remerbaach runs. Everything you learned about
structured output in week 2 transfers unchanged.

The second is that the failure modes do not transfer. This lab was built by
measuring before designing, and the measurements are in
`WEEK09_FINDINGS.md`. Two of them changed the session:

- The obvious implementation, one call for all six fields, has been observed
  failing three different ways, all silently, and then working on every call that followed. It is not broken. It is unreliable, which is
  worse, because it passes the test you were going to run.
- Downscaling a clean synthetic document is not degradation. All five
  invoices read perfectly at 40 percent scale. If your brittleness
  experiment is a resize, it measures nothing.

Read that file before block 2. It is short, and it will save you from
concluding something the numbers do not support.

## Learning outcomes exercised

Outcome 5 (describing how vision-language models extend the LLM paradigm and
identifying failure modes specific to multimodal inputs), outcome 6
(decomposing a problem into a system architecture and justifying the chosen
pattern composition), outcome 10 (integrating a vision-language model into
an agentic application that processes images, and validating its outputs
against multimodal failure modes), and outcome 12 (justifying trade-offs in
cost, latency, reliability, and safety). This is the ninth increment of the
project deliverable.

## Before you arrive

Read the multimodal use cases section of AIE-Huyen chapter 1 and the
foundation-model view in chapter 2.

Then run the setup, because the model is a 3.3 GB download and doing it in
the room wastes the block. The image library is new this week, and every script in `starter/` depends on it:

```bash
ollama pull qwen3-vl:4b
pip install "pillow>=11.0"
```

Open all six images in `images/` and look at them for two minutes. Two
minutes of looking prevents thirty minutes of debugging an extraction
against an image nobody has seen. `images/ground_truth.json` was written by
the same code that rendered the pixels, so it is exact by construction. Use
it to score. Never put it in a prompt.

## Timing

| Time | Block | What you do |
| 0 to 8 | Set up | Install, look at the six images, read the three failures in `WEEK09_FINDINGS.md` |
| 8 to 45 | Extract and check | TODO 1, 2, and 3, then `01_extract.py` |
| 45 to 50 | Start the long run | `python 02_break.py --sweep` live, then keep working while it runs |
| 50 to 72 | Break it | TODO 4, read the sweep, and the architecture comparison |
| 72 to 85 | Untrusted input | TODO 5, then `03_untrusted.py` |
| 85 to 90 | Close | Commit, push, and write `DECISIONS.md` |

The live sweep takes about six minutes and the full extraction pass about
six more. Start them and carry on; do not sit and watch. Every script takes
`--replay` and reads the recorded run in `fixtures/vision_runs.jsonl`
instead, which is instant and is what you use if the model is slow, your
laptop is busy, or you are catching up.

## What you build

Five files, six TODO markers.

| File | Marker | What it is |
| `vision.py` | TODO 1 | `guard`, the function that refuses a bad response |
| `vision.py` | TODO 2 | the call itself |
| `checks.py` | TODO 3 | four deterministic checks, none of them a model |
| `perturb.py` | TODO 4a, 4b | JPEG and blur, so the sweep degrades realistically |
| `03_untrusted.py` | TODO 5 | the gate predicate, in code |

TODO 1 is the one that matters. Every failure this model produces arrives as
HTTP 200, and two of the three arrive with `done_reason: stop`, which is the
API telling you nothing went wrong. If you only catch exceptions you will
catch nothing at all.

## The number that matters

`01_extract.py` prints five outcomes per run. Only one of them is a defect
you could not have found without opening the image:

| outcome | meaning |
| `correct` | every amount right, no check fired |
| `false_alarm` | every amount right, but a check fired anyway |
| `caught` | an amount wrong, and a check fired. The system working. |
| `WRONG` | an amount wrong, and every check passed |
| `refused` | no usable amount came back, which is at least honest |

`WRONG` is the column to read first. A pipeline with a high `correct` count
and one `WRONG` is more dangerous than one with a high `refused` count,
because the first kind ships a number into a ledger and the second kind asks
a human.

A warning you will need in block 1: an arithmetic check catches
INCONSISTENCY, not error. Three amounts that are all wrong but agree with
each other pass every check in the file. Work out on paper what
`net = 1180.80, vat = 200.74, total = 1381.54` does to your checks before
you decide they are finished.

## What to expect, so you do not misread it

Block 1 will very likely give you five correct and zero of everything else.
That is not success, it is an untested instrument. A check that has never
fired has not been tested, and the first thing block 2 does is make them
fire.

In block 2 the sweep will show four rows where nothing changes. Say why that
is a result rather than a broken experiment. Then find the one document that
fails first and say what is different about it. The operating limit belongs
to your worst document, not to your model, and a single number for "our
system works down to X" hides that.

## Homework

Two things, both small.

Run the sweep on one document of your own, photographed rather than
rendered, and say where it sits relative to the five here. A real photograph
has all the degradations at once and is the honest test.

Then wire today's `code_triage` to the week 8 approval gate, so that a failed
check routes to the human rather than printing a verdict. That is about ten
lines, and it is the sentence in your report that connects the two weeks:
what fires the gate is not model confidence, it is the failure of a
deterministic check.
