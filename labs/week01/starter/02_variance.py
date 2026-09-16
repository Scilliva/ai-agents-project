"""Block 3. Does the model repeat itself, and does temperature decide?

    python 02_variance.py --replay        # the shipped recording, no model
    python 02_variance.py                 # your own machine, two cells
    python 02_variance.py --full          # all eight cells, homework

Start with `--replay`. It reads a recording of ninety-six runs made on the
teaching machine and costs nothing, so the whole room is looking at the same
numbers while we discuss them. Then run your own two cells and see whether
your machine agrees.

The recording is real. `make_fixture.py` in the lab folder is what produced
it, and you can regenerate it yourself.

Three TODO markers.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from collections import Counter
from pathlib import Path

from project.fixtures import find_fixture
from project.models import BASE_URL, API_KEY, SMALL
from project.trace import write_json

FIXTURE = find_fixture("reference_runs.json", __file__,
                       lab="week01_setup_and_first_call")

# The two cells you run live. They are chosen because they disagree.
LIVE_CELLS = {
    "closed_short": "What is the capital of Luxembourg? Answer in one word.",
    "open_list": "List three responsibilities of a Luxembourg commune "
                 "administration. Be concise.",
}
LIVE_RUNS = 6


# --------------------------------------------------------------------------

def count_distinct(texts: list[str]) -> int:
    """TODO 4. How many genuinely different answers are in this list?

    Start with exact string equality, which is what a naive unit test would
    assert. Return the number of distinct strings.

    Then, before you move on, look at the strings themselves for the
    `open_list` cell and ask a harder question: how many are different in
    *wording* but identical in *meaning*? You cannot compute that here, and
    noticing that you cannot is the point. Week 10 spends the whole session
    on it.
    """
    raise NotImplementedError("TODO 4: count the distinct strings")


def summarize(cell_name: str, texts: list[str], latencies: list[float]) -> dict:
    return {
        "cell": cell_name,
        "n": len(texts),
        "distinct": count_distinct(texts),
        "mean_chars": int(statistics.mean(len(t) for t in texts)),
        "median_latency_s": round(statistics.median(latencies), 3),
        "min_latency_s": round(min(latencies), 3),
        "max_latency_s": round(max(latencies), 3),
    }


# --------------------------------------------------------------------------

def from_replay(full: bool) -> list[dict]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    print(f"Recording: {payload['meta']['model']} on "
          f"{payload['meta']['machine']}, "
          f"{payload['meta']['recorded_at']}\n")
    rows = []
    for name, cell in payload["cells"].items():
        if not full and not name.startswith(tuple(LIVE_CELLS)):
            continue
        texts = [r["text"] for r in cell["runs"]]
        lats = [r["latency_s"] for r in cell["runs"]]
        rows.append(summarize(name, texts, lats))
    return rows


def from_live(full: bool) -> list[dict]:
    from openai import OpenAI
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    rows = []
    for pname, prompt in LIVE_CELLS.items():
        for tname, temp in (("t00", 0.0), ("t10", 1.0)):
            texts, lats = [], []
            for _ in range(LIVE_RUNS):
                t0 = time.perf_counter()
                reply = client.chat.completions.create(
                    model=SMALL.name, temperature=temp, max_tokens=200,
                    messages=[{"role": "user", "content": prompt}])
                lats.append(time.perf_counter() - t0)
                texts.append(reply.choices[0].message.content.strip())
            rows.append(summarize(f"{pname}|{tname}", texts, lats))
    return rows


# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true",
                    help="read the shipped recording instead of calling")
    ap.add_argument("--full", action="store_true",
                    help="all eight cells rather than the live two")
    args = ap.parse_args()

    rows = from_replay(args.full) if args.replay else from_live(args.full)

    print(f"{'cell':<24} {'distinct':>10} {'chars':>7} {'median s':>10}")
    print("-" * 54)
    for r in rows:
        print(f"{r['cell']:<24} {r['distinct']:>7}/{r['n']} "
              f"{r['mean_chars']:>7} {r['median_latency_s']:>10.2f}")

    write_json("artifacts/week01_variance.json",
               {"source": "replay" if args.replay else "live", "rows": rows})

    # TODO 5. Compare the recording against your own machine.
    #
    #   Run this file twice, once with --replay and once without, and put
    #   the two `distinct` columns side by side.
    #
    #   Three questions to answer in DECISIONS.md:
    #     a. At temperature 0, how many distinct answers did you get? Does
    #        your machine agree with the recording?
    #     b. At temperature 1.0, one of the two cells still returns a single
    #        distinct answer. Which one, and why that one? The answer is not
    #        "the temperature did not work".
    #     c. A unit test asserting exact string equality would pass on some
    #        of these cells and fail on others. Name which, and say what
    #        that tells you about testing this system.

    # TODO 6. Then write down the one sentence that carries into week 10.
    #
    #   You will be tempted to write "the model is random". Resist it, the
    #   evidence above does not say that. Write instead what the evidence
    #   does say about when you can and cannot rely on repeating an output.
    #   Week 10 will ask you to find this sentence again.

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
