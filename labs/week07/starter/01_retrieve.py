"""Index, retrieve, diagnose, sweep chunk sizes, and try Q05 decomposition.

    python 01_retrieve.py --replay     # the recorded table, instant
    python 01_retrieve.py              # your own index, about 30 seconds

Diagnostic conclusions are printed from the measured table.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from chunking import load_chunks
from goldset import GOLD
from metrics import score
from retrieval import DenseIndex, keyword_search

from project.contracts import GoldCase, GoldSet
from project.fixtures import find_fixture, load_or_reference
from project.trace import write_json

LAB = "week07_rag_pipeline"
K = 5


def run_live(size: int = 600, overlap: int = 80) -> list[dict]:
    chunks = load_chunks(size=size, overlap=overlap)
    started = time.perf_counter()
    index = DenseIndex(chunks, name=f"s{size}")
    elapsed = time.perf_counter() - started
    print(f"{len(chunks)} chunks, {index.dim} dimensions, "
          f"indexing {elapsed:.2f}s\n")

    rows = []
    for question in GOLD:
        dense = index.search(question.question, k=len(chunks))
        keyword = keyword_search(chunks, question.question, k=len(chunks))
        d = score(dense, question, k=K)
        kw = score(keyword, question, k=K)
        rows.append({
            "qid": question.qid, "tags": list(question.tags),
            "answerable": question.answerable,
            "dense_rank": d.rank, "dense_recall": d.recall_at_k,
            "keyword_rank": kw.rank, "keyword_recall": kw.recall_at_k,
            "top5": d.retrieved,
        })
    return rows


def run_sweep(sizes: list[int], overlap: int) -> None:
    """Compare chunk sizes by question, retaining each configuration's rows."""
    results: dict[int, list[dict]] = {}
    for size in sizes:
        print(f"\n=== size={size}, overlap={overlap} ===")
        results[size] = run_live(size, overlap)
    by_size = {size: {row["qid"]: row for row in rows}
               for size, rows in results.items()}
    answerable = [q.qid for q in GOLD if q.answerable]
    for size in sizes[1:]:
        moved = [qid for qid in answerable if (
            by_size[size][qid]["dense_rank"] != by_size[sizes[0]][qid]["dense_rank"]
            or by_size[size][qid]["keyword_rank"] != by_size[sizes[0]][qid]["keyword_rank"])]
        print(f"Questions whose rank changes from size {sizes[0]} to {size}: "
              f"{', '.join(moved) if moved else 'none'}")
    write_json("artifacts/week07_chunk_sweep.json", {
        "sizes": sizes, "overlap": overlap,
        "baseline_size": sizes[0],
        "runs": {str(size): rows for size, rows in results.items()},
    })


def run_decomposed(size: int, overlap: int) -> None:
    """Try two targeted queries for Q05 and report merged section recall."""
    chunks = load_chunks(size=size, overlap=overlap)
    index = DenseIndex(chunks, name=f"s{size}_decomposed")
    subqueries = [
        "How many days after moving in must I declare my arrival?",
        "How do I apply for a resident parking vignette for my car?",
    ]
    retrieved = []
    for query in subqueries:
        hits = index.search(query, k=5)
        retrieved.extend(hits)
        sections = list(dict.fromkeys(
            f"{chunk.doc_id}::{chunk.section}" for chunk in hits))
        print(f"Query: {query}\n  top sections: {', '.join(sections)}")
    unique = list({chunk.chunk_id: chunk for chunk in retrieved}.values())
    q05 = next(question for question in GOLD if question.qid == "Q05")
    result = score(unique, q05, k=len(unique))
    found_sections = {chunk.key for chunk in unique}
    expected = {tuple(section.split("::", 1)) for section in q05.gold_sections}
    print(f"Merged Q05 sections: {len(expected & found_sections)}/{len(expected)}; "
          f"section recall={result.recall_at_k:.2f}; "
          f"embedding queries={len(subqueries)} (one original query)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--size", type=int, default=600)
    ap.add_argument("--overlap", type=int, default=80)
    ap.add_argument("--sweep", action="store_true",
                    help="run sizes 300, 600, and 1200 and compare per-question ranks")
    ap.add_argument("--decompose-q05", action="store_true",
                    help="try two focused retrieval queries for the compositional Q05")
    args = ap.parse_args()

    if args.sweep:
        run_sweep([300, 600, 1200], args.overlap)
        return 0
    if args.decompose_q05:
        run_decomposed(args.size, args.overlap)
        return 0
    if args.replay:
        path = find_fixture("reference_runs.json", __file__, lab=LAB)
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        print(f"replay: {payload['meta']['chunks']} chunks, "
              f"{payload['meta']['embed_model']}, "
              f"recorded {payload['meta']['recorded_at']}\n")
        rows = payload["rows"]
    else:
        rows = run_live(args.size, args.overlap)

    print(f"{'qid':<5}{'dense rank':>12}{'kw rank':>9}"
          f"{'dense R@' + str(K):>11}{'kw R@' + str(K):>9}   tags")
    print("-" * 72)
    for row in rows:
        if not row["answerable"]:
            print(f"{row['qid']:<5}{'unanswerable':>12}{'-':>9}{'-':>10}   "
                  f"{','.join(row['tags'])}")
            continue
        print(f"{row['qid']:<5}{str(row['dense_rank']):>12}"
              f"{str(row['keyword_rank']):>9}"
              f"{row['dense_recall']:>11.2f}"
              f"{row['keyword_recall']:>9.2f}   {','.join(row['tags'])}")

    answerable = [r for r in rows if r["answerable"]]
    found = [r for r in answerable if r["dense_rank"]]
    print(f"\n  dense: gold chunk in the top {K} on "
          f"{sum(1 for r in answerable if r['dense_recall'] > 0)}"
          f"/{len(answerable)} questions")
    print(f"  dense beats keyword on "
          f"{sum(1 for r in found if r['keyword_rank'] and r['dense_rank'] < r['keyword_rank'])}"
          f", keyword beats dense on "
          f"{sum(1 for r in found if r['keyword_rank'] and r['keyword_rank'] < r['dense_rank'])}")

    dense_first = sum(r["dense_rank"] == 1 for r in answerable)
    print(f"  interpretation: dense ranks first on {dense_first}/"
          f"{len(answerable)} answerable questions; treat this as evidence "
          "that this question set is easy, not a general quality guarantee")
    by_qid = {row["qid"]: row for row in rows}
    q05 = by_qid.get("Q05")
    if q05:
        print(f"  Q05: dense rank {q05['dense_rank']}, keyword rank "
              f"{q05['keyword_rank']}; it needs two sections from separate "
              "documents, so changing chunk size alone does not decompose it")
    dense_advantages = [r for r in answerable
                        if r["dense_rank"] and r["keyword_rank"]
                        and r["dense_rank"] < r["keyword_rank"]]
    if dense_advantages:
        biggest = max(dense_advantages,
                      key=lambda r: r["keyword_rank"] - r["dense_rank"])
        print(f"  largest dense advantage: {biggest['qid']} "
              f"({biggest['dense_rank']} vs {biggest['keyword_rank']})")
    q02 = by_qid.get("Q02")
    if q02:
        print(f"  Q02 gold note check: dense rank {q02['dense_rank']}, "
              f"keyword rank {q02['keyword_rank']}")

    write_json("artifacts/week07_retrieval.json", {"k": K, "rows": rows})

    # Diagnostic conclusions for DECISIONS.md (use your own live ranks;
    # the fixture's recorded ranks may differ slightly by Chroma version):
    # ten first-place results indicate an easy, narrowly constructed task,
    # not proof of a generally good retrieval pipeline. Q05 is compositional:
    # its answer needs the arrival deadline and vignette application from
    # separate sections/documents. A single query ranked as one vector may
    # miss either; changing chunk size cannot supply the missing query
    # decomposition. Q02's note in goldset.py has been corrected: this run
    # places dense first and keyword fourth, with both in the top five.
    # Compare the table to name the largest dense advantage.
    existing, source = load_or_reference("goldset.json", lab=LAB)
    print(f"\ngold set loaded from: {source}")
    goldset = GoldSet.model_validate(existing)
    already = {c.case_id for c in goldset.cases}
    for question in GOLD:
        if question.qid in already:
            continue
        goldset.cases.append(GoldCase(
            case_id=question.qid, week_added=7, question=question.question,
            expected={"gold_sections": list(question.gold_sections)},
            expected_behavior=(
                "answers from the named sections and cites them"
                if question.answerable
                else "refuses, because the corpus cannot answer it"),
            slice_tags=["task:retrieval", *question.tags],
            must_refuse=not question.answerable))
    write_json("artifacts/goldset.json", goldset)
    print(f"gold set now holds {len(goldset.cases)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
