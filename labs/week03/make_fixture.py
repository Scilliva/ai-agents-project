"""Record the week 3 replay fixture.

    python make_fixture.py

Records every call the session makes: the monolith over all 24 queries, the
router's classify and respond calls, both models for the model-routing
variant, and three temperature 0.7 samples per query for the voting variant.

Nothing here is edited by hand. The confusions, the paraphrased evidence
spans, and the larger model's refusal to report a confidence below 0.80 are
all real behavior of the reference models on this corpus.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "solution"))

from queries import QUERIES                                   # noqa: E402
from router import classify, respond                          # noqa: E402
from routes import SPECIALISTS, SYSTEM_MONOLITH               # noqa: E402
from openai import OpenAI                                     # noqa: E402

from project.fixtures import RecordingClient                  # noqa: E402
from project.models import BASE_URL, API_KEY, LARGE, SMALL    # noqa: E402

OUT = Path(__file__).parent / "fixtures" / "replay.json"
VOTE_TEMPERATURES = (0.7, 1.0, 1.5)


def main() -> int:
    # Start clean. RecordingClient appends, which is what makes
    # multi-sample recording work, and it also means re-running this
    # over an existing file would double every response list.
    OUT.unlink(missing_ok=True)
    inner = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    rec = RecordingClient(
        inner, OUT,
        model=f"{SMALL.name} and {LARGE.name}",
        recorded_at=time.strftime("%Y-%m-%d"),
        machine="Apple M4, 16 GB, Ollama, one request at a time",
        planted_failures=[
            "the small model sends 2 requests and 2 others into info",
            "the large model paraphrases the evidence span 4 times in 24",
            "the large model reports only two distinct confidence values, "
            "both above 0.95, so no threshold can do useful work on it",
            "three votes at temperature 0.7 and 1.0 never disagree at all, "
            "so voting costs three times as much and changes nothing",
        ],
        note="Real model output, unedited.",
    )

    t0 = time.perf_counter()
    for q in QUERIES:
        respond(rec, SYSTEM_MONOLITH, q.text, SMALL.name)
    print(f"  monolith          {len(QUERIES):>3} calls "
          f"{time.perf_counter() - t0:6.1f}s")

    t0 = time.perf_counter()
    for q in QUERIES:
        decision, _ = classify(rec, q.text, SMALL.name)
        for route in SPECIALISTS:
            # Every specialist, so the fixture covers whatever route a
            # student's own policy layer ends up choosing. Without this, a
            # student whose threshold differs from the reference gets a
            # fixture miss on a perfectly reasonable decision.
            respond(rec, SPECIALISTS[route], q.text, SMALL.name)
    print(f"  router            {len(QUERIES) * 6:>3} calls "
          f"{time.perf_counter() - t0:6.1f}s")

    t0 = time.perf_counter()
    for q in QUERIES:
        classify(rec, q.text, LARGE.name)
    print(f"  large classifier  {len(QUERIES):>3} calls "
          f"{time.perf_counter() - t0:6.1f}s")

    t0 = time.perf_counter()
    for temp in VOTE_TEMPERATURES:
        for q in QUERIES:
            for _ in range(3):
                classify(rec, q.text, SMALL.name, temperature=temp)
    n = len(QUERIES) * 3 * len(VOTE_TEMPERATURES)
    print(f"  voting samples    {n:>3} calls "
          f"{time.perf_counter() - t0:6.1f}s")

    path = rec.save()
    print(f"\nwrote {path} ({len(rec.records)} recordings, "
          f"{path.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
