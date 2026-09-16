"""The models this course runs on, and how to reach them.

Everything runs locally. There is no key, no bill, and no rate limit, which
means you can rerun an experiment two hundred times without asking anyone's
permission. That is the point: this course asks you to measure things, and
measuring means repeating.

Models are named by role rather than by name everywhere else in your code.
Write `client_for(SMALL)`, not `client_for("qwen3:4b-instruct")`. Swapping
the model then costs one line, and swapping the model is an experiment you
will run in weeks 2, 3, 5, 9, and 10.

The endpoint speaks the OpenAI wire format. That is deliberate. Weeks 1 to 4
call it by hand with the `openai` SDK so you see the mechanics, and from
week 5 Pydantic AI makes the same calls for you. Nothing changes underneath,
which is exactly the point of adopting a framework only after you have
written the loop yourself.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

BASE_URL = "http://127.0.0.1:11434/v1"
OLLAMA_URL = "http://127.0.0.1:11434"
API_KEY = "ollama"          # required by the SDK, ignored by the server


@dataclass(frozen=True)
class ModelSpec:
    """A model, and the facts about it you will be asked to justify.

    The numbers were measured on an Apple M4 with 16 GB in August 2026.
    They are here so that a design argument can quote something, and they
    are wrong on your machine, which is the first thing week 1 asks you to
    find out. Replace them with your own.
    """

    name: str
    role: str
    disk_gb: float
    resident_gb: float
    median_latency_s: float
    note: str


SMALL = ModelSpec(
    name="qwen3:4b-instruct", role="text",
    disk_gb=2.5, resident_gb=3.9, median_latency_s=1.1,
    note="Weeks 1 to 3. Extraction and classification. Measured better than "
         "LARGE at routing (20/24 against 17/24) and it copies verbatim "
         "spans more faithfully.")

LARGE = ModelSpec(
    name="qwen2.5:7b", role="text",
    disk_gb=4.7, resident_gb=5.0, median_latency_s=2.5,
    note="Weeks 4 onward. Tool loops. Measured much better than SMALL at "
         "driving a ReAct loop (7/10 against 4/10), which is the opposite "
         "of the week 3 result and the reason both are required.")

EMBED = ModelSpec(
    name="nomic-embed-text:latest", role="embedding",
    disk_gb=0.27, resident_gb=0.5, median_latency_s=0.05,
    note="768 dimensions. Week 7 treats it as a black box, which is what "
         "the syllabus asks for.")

VISION = ModelSpec(
    name="qwen3-vl:4b", role="vision",
    disk_gb=3.3, resident_gb=4.0, median_latency_s=7.4,
    note="Week 9. Note the latency: an image is not a cheap input, and a "
         "sweep over six images at three resolutions is eighteen calls.")

# Which model each week needs. Both text models are required, and which one
# is right is a per-task question rather than a quality ladder. The course
# makes that argument with two measurements that point in opposite
# directions:
#
#   week 3, routing 24 queries    SMALL 20/24   LARGE 17/24
#   week 4, a ReAct tool loop     SMALL  4/10   LARGE  7/10
#
# Classification wants the model that follows a narrow instruction closely.
# A tool loop wants the model that can hold a plan across several steps.
# Those are not the same thing, and "use the bigger model" is not a strategy.
REQUIRED = [SMALL, EMBED, LARGE]   # about 7.5 GB of disk
OPTIONAL = [VISION]                # week 9
ALL_MODELS = REQUIRED + OPTIONAL

# Resident sizes above are measured at COURSE_CONTEXT_LENGTH. On an 8 GB
# machine the two text models fit one at a time and not together, so loading
# one evicts the other. That is the cold start you measured in week 1
# arriving as an architectural constraint, and it is why no session asks you
# to switch models inside a single request.


# --------------------------------------------------------------------------
# Reaching the endpoint
# --------------------------------------------------------------------------

def client_for(spec: ModelSpec | str = SMALL):
    """An OpenAI SDK client pointed at the local server.

    Returns the client only. The model name is yours to pass at call time,
    which keeps the "same client, different model" comparison one argument
    wide.
    """
    from openai import OpenAI            # imported here so that
    return OpenAI(base_url=BASE_URL,     # `python -m project.verify` works
                  api_key=API_KEY)       # without the SDK installed

def model_name(spec: ModelSpec | str) -> str:
    return spec.name if isinstance(spec, ModelSpec) else spec


def pydantic_ai_model(spec: ModelSpec | str = SMALL):
    """The same endpoint, wrapped for Pydantic AI. Week 5 onward."""
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.ollama import OllamaProvider
    return OpenAIChatModel(model_name(spec),
                           provider=OllamaProvider(base_url=BASE_URL))


# --------------------------------------------------------------------------
# Preflight, used by week 1 and by anyone whose lab suddenly stops working
# --------------------------------------------------------------------------

def server_is_up(timeout: float = 3.0) -> bool:
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags",
                                    timeout=timeout) as r:
            return r.status == 200
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def installed_models(timeout: float = 5.0) -> list[str]:
    with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=timeout) as r:
        body = json.loads(r.read())
    return [m["name"] for m in body.get("models", [])]


# The context window the course runs at. Every prompt in these labs fits
# inside it with room to spare: the longest is week 7's retrieved passages,
# which reach about four thousand tokens.
#
# This is not a tuning preference, it is the single most important setting on
# your machine. Left unset, Ollama sizes the key-value cache for the model's
# maximum context, and two of the course models advertise 262144. Measured on
# the teaching machine:
#
#   qwen3:4b-instruct, default 262144 :  42 GB reserved, 77 per cent on CPU
#   qwen3:4b-instruct, set to 8192    : 3.8 GB reserved, 100 per cent on GPU
#
# Eleven times the memory, for context you will never use. On a 16 GB machine
# it merely spills to the CPU and runs slowly. On an 8 GB machine it is the
# difference between the course working and not working.
COURSE_CONTEXT_LENGTH = 8192
CONTEXT_WARN_ABOVE = 32768


def loaded_models(timeout: float = 5.0) -> list[dict]:
    """What is resident right now, with size and context. Empty if none."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/ps",
                                    timeout=timeout) as r:
            return json.loads(r.read()).get("models", [])
    except (urllib.error.URLError, OSError, TimeoutError, ValueError):
        return []


def check_context_budget() -> list[str]:
    """Warn if a resident model reserved far more memory than it needs.

    Returns a list of plain-language problems, empty when all is well. Call
    it after something has been loaded, because nothing is resident until
    the first call.
    """
    problems: list[str] = []
    for m in loaded_models():
        ctx = m.get("context_length") or 0
        if ctx <= CONTEXT_WARN_ABOVE:
            continue
        gb = m.get("size", 0) / 1e9
        problems.append(
            f"{m.get('name', 'a model')} is resident with a context window "
            f"of {ctx:,} tokens and is reserving {gb:.1f} GB.\n"
            f"  This course never uses more than about 4,000 tokens, so that "
            f"memory is wasted and\n"
            f"  on a smaller machine it will push the model onto the CPU and "
            f"make everything slow.\n"
            f"  Fix it by starting the server with an explicit context "
            f"length:\n"
            f"    macOS or Linux:  OLLAMA_CONTEXT_LENGTH="
            f"{COURSE_CONTEXT_LENGTH} ollama serve\n"
            f"    macOS app:       launchctl setenv OLLAMA_CONTEXT_LENGTH "
            f"{COURSE_CONTEXT_LENGTH}, then restart Ollama\n"
            f"    Windows:         setx OLLAMA_CONTEXT_LENGTH "
            f"{COURSE_CONTEXT_LENGTH}, then restart Ollama")
    return problems


def preflight(require_optional: bool = False) -> tuple[bool, list[str]]:
    """Is this machine ready? Returns (ok, list of problems in plain words).

    Written to be readable rather than clever, because the person reading
    its output is stuck and probably annoyed.
    """
    problems: list[str] = []
    if not server_is_up():
        return False, [
            "The model server is not answering on " + OLLAMA_URL + ".",
            "Start it with `ollama serve`, or open the Ollama application.",
        ]

    have = set(installed_models())
    wanted = ALL_MODELS if require_optional else REQUIRED
    for spec in wanted:
        # Ollama reports `name:tag`, and a bare name means the latest tag.
        if spec.name in have or f"{spec.name}:latest" in have:
            continue
        problems.append(
            f"Missing {spec.name} ({spec.disk_gb} GB). "
            f"Pull it with `ollama pull {spec.name}`.")
    return not problems, problems
