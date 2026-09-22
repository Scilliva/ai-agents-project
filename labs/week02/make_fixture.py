"""Record the week 2 replay fixture.

You do not need to run this. `fixtures/replay.json` ships with the lab, and
the point of it is that your scorer runs in under a second instead of
forty-five while you are still writing it.

    python make_fixture.py

It records every call both variants make, plus the sensitivity variants, so
that the whole session can be done with no model at all.

The fixture contains real failures. Nothing is edited or planted by hand:
the reference model genuinely invents due dates for messages that state
none, and genuinely stops copying quotes verbatim once the example block
shows it a tidied one. Those are the two most instructive results of the
session and they are in here because they happened.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "solution"))

from documents import DOCS, GOLD                              # noqa: E402
from extractor import SYSTEM_ZERO_SHOT, extract               # noqa: E402
from openai import OpenAI                                     # noqa: E402

from project.fixtures import RecordingClient                  # noqa: E402
from project.models import BASE_URL, API_KEY, SMALL           # noqa: E402

OUT = Path(__file__).parent / "fixtures" / "replay.json"


def main() -> int:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "few_shot_mod", Path(__file__).parent / "solution" / "02_few_shot.py")
    few = importlib.util.module_from_spec(spec)
    sys.modules["few_shot_mod"] = few
    spec.loader.exec_module(few)

    spec3 = importlib.util.spec_from_file_location(
        "sens_mod", Path(__file__).parent / "solution" / "03_sensitivity.py")
    sens = importlib.util.module_from_spec(spec3)
    sys.modules["sens_mod"] = sens
    spec3.loader.exec_module(sens)

    inner = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    rec = RecordingClient(
        inner, OUT,
        model=SMALL.name,
        recorded_at=time.strftime("%Y-%m-%d"),
        machine="Apple M4, 16 GB, Ollama, one request at a time",
        planted_failures=[
            "zero-shot invents due dates on messages that state none",
            "zero-shot confuses facilities with access on REQ-04",
            "the quote field gets worse under few-shot if examples "
            "show tidied quotes",
        ],
        note="Real model output, unedited. Nothing here was written by hand.",
    )

    systems = [
        ("zero-shot", SYSTEM_ZERO_SHOT),
        ("few-shot", few.SYSTEM_FEW_SHOT),
    ]
    for variant in ("role", "reordered", "no_delimiter", "english_only"):
        systems.append((variant, sens.build_system(variant)))

    for label, system in systems:
        t0 = time.perf_counter()
        for doc in DOCS:
            extract(rec, system, doc.text)
        print(f"  recorded {label:<14} {len(DOCS)} calls "
              f"in {time.perf_counter() - t0:5.1f}s")

    path = rec.save()
    size_kb = path.stat().st_size / 1024
    print(f"\nwrote {path} ({len(rec.records)} recordings, {size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
