"""Record the week 7 reference retrieval table.

    python make_fixture.py

Records the rank of the first gold chunk for both retrievers on all twelve
questions, so the whole room discusses the same numbers even when their own
index differs. Embedding the corpus takes about two seconds, so this is
quick.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "solution"))

from chunking import load_chunks                             # noqa: E402
from project.models import EMBED                             # noqa: E402

OUT = Path(__file__).parent / "fixtures" / "reference_runs.json"


def main() -> int:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "retr_mod", Path(__file__).parent / "solution" / "01_retrieve.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["retr_mod"] = mod
    spec.loader.exec_module(mod)

    t0 = time.perf_counter()
    rows = mod.run_live()
    chunks = load_chunks()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "meta": {
            "embed_model": EMBED.name, "chunks": len(chunks),
            "chunk_size": 600, "overlap": 80, "k": mod.K,
            "recorded_at": time.strftime("%Y-%m-%d"),
            "machine": "Apple M4, 16 GB, Ollama, Chroma in memory",
            "what_to_notice": [
                "ten of eleven answerable questions rank the gold chunk "
                "first, which says the task is easy rather than that the "
                "pipeline is good",
                "Q05 needs two documents and fails on both retrievers",
                "Q02 contradicts its own note in goldset.py: dense ranks it "
                "first and keyword twelfth",
            ],
        },
        "rows": rows,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT} in {time.perf_counter() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
