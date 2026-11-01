"""Small CLI smoke path for the Week 7 memory search integration."""

from __future__ import annotations

import argparse

from .memory import MemoryStore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", required=True)
    parser.add_argument("query", nargs="+")
    args = parser.parse_args()

    store = MemoryStore.load()
    hits = store.search(args.subject, " ".join(args.query), k=5)
    print(f"memory.search ({args.subject}): {len(hits)} hits")
    for hit in hits:
        print(f"- {hit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
