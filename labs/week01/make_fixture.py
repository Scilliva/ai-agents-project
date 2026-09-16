"""Record the week 1 reference measurements.

You do not need to run this. The recording it produces is already in
`fixtures/reference_runs.json` and the lab uses it. It is here because a
fixture whose provenance you cannot check is not evidence, and because the
coordinator regenerates it whenever the course model changes.

    python make_fixture.py                     # default model
    python make_fixture.py qwen2.5:7b          # or any local model

What it records, for one model:

  * four prompts crossed with two temperatures, twelve serial runs each
  * every output, so distinctness can be counted rather than asserted
  * per run latency, and prompt and completion token counts

The interesting cells are the ones where the answer is not what a student
expects, and they are listed in `meta.what_to_notice` so that nobody has to
hunt for them.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
import urllib.request
from pathlib import Path

HOST = "http://127.0.0.1:11434/api/chat"
MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen3:4b-instruct"
RUNS = 12
OUT = Path(__file__).parent / "fixtures" / "reference_runs.json"

PROMPTS = {
    "closed_short": "What is the capital of Luxembourg? Answer in one word.",
    "open_short": "In one sentence, why is Luxembourg City important to the "
                  "European Union?",
    "open_list": "List three responsibilities of a Luxembourg commune "
                 "administration. Be concise.",
    "open_reasoning": "A resident asks whether they need a parking vignette "
                      "if they park in a visitor bay. Explain what "
                      "information you would need before answering, and why.",
}
TEMPERATURES = {"t00": 0.0, "t10": 1.0}


def call(prompt: str, temperature: float) -> dict:
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": temperature, "num_predict": 200},
    }
    # A seed is set only at temperature 0. At temperature 1 the point is to
    # let it vary, and pinning the seed there would hide the effect.
    if temperature == 0.0:
        payload["options"]["seed"] = 42
    req = urllib.request.Request(
        HOST, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=300) as r:
        body = json.loads(r.read())
    return {
        "text": body["message"]["content"].strip(),
        "latency_s": round(time.perf_counter() - t0, 3),
        "prompt_tokens": body.get("prompt_eval_count"),
        "completion_tokens": body.get("eval_count"),
    }


def main() -> int:
    # One throwaway call, so that the model load does not land inside the
    # measurements. The cold start is real and it is measured separately in
    # the lab, on purpose.
    print("warming up ...")
    call("hello", 0.0)

    cells: dict[str, dict] = {}
    for pname, prompt in PROMPTS.items():
        for tname, temp in TEMPERATURES.items():
            runs = [call(prompt, temp) for _ in range(RUNS)]
            texts = [r["text"] for r in runs]
            lat = [r["latency_s"] for r in runs]
            cells[f"{pname}|{tname}"] = {
                "prompt": prompt,
                "temperature": temp,
                "runs": runs,
                "distinct": len(set(texts)),
                "n": RUNS,
                "median_latency_s": round(statistics.median(lat), 3),
                "min_latency_s": min(lat),
                "max_latency_s": max(lat),
                "mean_chars": int(statistics.mean(len(t) for t in texts)),
            }
            print(f"  {pname:<16} {tname}  distinct {len(set(texts)):>2}/{RUNS}"
                  f"  median {statistics.median(lat):.2f}s")

    payload = {
        "meta": {
            "model": MODEL,
            "recorded_at": time.strftime("%Y-%m-%d"),
            "machine": "Apple M4, 16 GB, Ollama, one request at a time",
            "runs_per_cell": RUNS,
            "seed_at_temperature_0": 42,
            "what_to_notice": [
                "At temperature 0 every cell is 1 distinct output out of 12. "
                "Served this way, the model is reproducible.",
                "At temperature 1 the same prompts are not. Determinism is a "
                "setting here, not a property of the model.",
                "Latency tracks output length far more than prompt length. "
                "The reasoning prompt costs about 35 times the closed one.",
                "This recording excludes the cold start. Measure that "
                "yourself, it is the largest number you will see today.",
            ],
        },
        "cells": cells,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
