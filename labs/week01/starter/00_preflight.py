"""Is this machine ready? Run this first. There is nothing to complete here.

    python 00_preflight.py

It checks four things and tells you what to do about each one in plain
words. Its job is to separate an environment problem from a code problem
before you write any code, because those two failures look identical from
inside a traceback and take very different amounts of time to fix.

If it fails, ask after five minutes of trying, not after nineteen.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def check(label: str, ok: bool, fix: str = "") -> bool:
    print(f"[{'ok  ' if ok else 'FAIL'}] {label}")
    if not ok and fix:
        for line in fix.splitlines():
            print(f"       {line}")
    return ok


def main() -> int:
    print("Week 1 preflight\n")
    results = []

    # 1. Python version. Pydantic and the SDK both want a recent one.
    v = sys.version_info
    results.append(check(
        f"Python {v.major}.{v.minor}.{v.micro}",
        (v.major, v.minor) >= (3, 11),
        "This course assumes Python 3.11 or later.\n"
        "Install a newer Python and recreate your virtual environment."))

    # 2. The project spine, which every later week imports.
    try:
        import project                                        # noqa: F401
        from project import models
        results.append(check("project spine importable", True))
    except ImportError:
        results.append(check(
            "project spine importable", False,
            "Unpack project_spine.zip from Moodle, copy the package to the\n"
            "root of your repository, and install it into your venv:\n"
            "  cp -r project_spine/project ./project\n"
            "  cp project_spine/pyproject.toml . && pip install -e .\n"
            "then run this script again from the repository root."))
        print("\nStopping here, the remaining checks need the spine.")
        return 1

    # 3. The dependencies this week uses.
    for mod, why in (("openai", "the SDK you call the local endpoint with"),
                     ("pydantic", "the schemas in project/contracts.py")):
        try:
            __import__(mod)
            results.append(check(f"{mod} installed", True))
        except ImportError:
            results.append(check(f"{mod} installed", False,
                                 f"Needed for {why}.\n"
                                 f"  pip install -r requirements.txt"))

    # 4. The model server, and the models themselves.
    if shutil.which("ollama") is None:
        results.append(check(
            "ollama on PATH", False,
            "Install it from https://ollama.com, then reopen your terminal.\n"
            "Everything in this course runs locally, so this is the one\n"
            "piece of infrastructure you need."))
    else:
        results.append(check("ollama on PATH", True))

    ok, problems = models.preflight()
    if ok:
        results.append(check("model server and required models", True))
    else:
        results.append(check("model server and required models", False,
                             "\n".join(problems)))

    # 5. The memory setting that matters more than any other. Nothing is
    # resident until something has been called, so load the model first and
    # then look at what it reserved.
    if ok:
        try:
            from openai import OpenAI
            OpenAI(base_url=models.BASE_URL,
                   api_key=models.API_KEY).chat.completions.create(
                model=models.SMALL.name, max_tokens=1,
                messages=[{"role": "user", "content": "hi"}])
        except Exception:                                     # noqa: BLE001
            pass
        context_problems = models.check_context_budget()
        results.append(check("context window sized sensibly",
                             not context_problems,
                             "\n".join(context_problems)))

    # A note rather than a check. The optional models are wanted from week 9,
    # and pulling them now on fast network beats pulling them on lab day.
    ok_all, _ = models.preflight(require_optional=True)
    if ok and not ok_all:
        print("\n[note] The optional models are not installed yet. You do "
              "not\n       need them today. Pull them before week 9:")
        for spec in models.OPTIONAL:
            print(f"         ollama pull {spec.name}    # {spec.disk_gb} GB")

    print()
    if all(results):
        print("Ready. Continue with 01_first_call.py.")
        return 0
    print("Not ready yet. Fix the FAIL lines above, in order, then rerun.")
    print("If a model is still downloading, that is fine: start on")
    print("02_variance.py, which runs against the shipped recording and")
    print("needs no model at all.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
