"""Is week 7's retrieval measurable and interesting on the local embedder?

Three questions:
  1. Does nomic-embed-text retrieve these 12 gold questions usefully?
  2. Are the numbers in the band that makes a session work? Recall at 20
     near 1.0 with precision at 5 well below it is ideal: it gives students
     a real trade-off rather than a flat pass or a flat fail.
  3. Do the TAGGED questions behave as the gold set claims? The rare-token
     one should be where dense retrieval loses to keyword search, and the
     vocabulary one should be where it wins. If those two do not separate,
     the week's best discussion is not in the data.

Usage:  python retrieval_probe.py, from this folder, with solution/ present
"""

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB / "solution"))

from goldset import GOLD                                     # noqa: E402

EMBED_URL = "http://127.0.0.1:11434/api/embed"
EMBED_MODEL = "nomic-embed-text:latest"


# --------------------------------------------------------------------------
# corpus -> chunks, keeping doc_id and section
# --------------------------------------------------------------------------

def load_chunks(size: int = 600, overlap: int = 80):
    chunks = []
    for path in sorted((LAB / "corpus").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta = {}
        if text.startswith("---"):
            head, _, text = text.partition("---\n")[2].partition("---\n")
            for line in head.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    meta[k.strip()] = v.strip()
        doc_id = meta.get("doc_id", path.stem)

        section = "(intro)"
        buf: list[str] = []
        def flush():
            body = "\n".join(buf).strip()
            if not body:
                return
            step = max(1, size - overlap)
            for i in range(0, len(body), step):
                piece = body[i:i + size]
                if piece.strip():
                    chunks.append({"doc_id": doc_id, "section": section,
                                   "text": f"{section}\n{piece}"})
        for line in text.splitlines():
            if line.startswith("## "):
                flush(); buf = []; section = line[3:].strip()
            else:
                buf.append(line)
        flush()
    return chunks


def embed(texts: list[str]) -> list[list[float]]:
    out = []
    for i in range(0, len(texts), 32):
        req = urllib.request.Request(
            EMBED_URL,
            data=json.dumps({"model": EMBED_MODEL,
                             "input": texts[i:i + 32]}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as r:
            out.extend(json.loads(r.read())["embeddings"])
    return out


def cosine(a, b):
    num = sum(x * y for x, y in zip(a, b))
    da = sum(x * x for x in a) ** 0.5
    db = sum(x * x for x in b) ** 0.5
    return num / (da * db) if da and db else 0.0


def keyword_rank(chunks, query, k):
    terms = {t.lower() for t in re.findall(r"[\w-]+", query) if len(t) > 2}
    scored = []
    for i, c in enumerate(chunks):
        words = {w.lower() for w in re.findall(r"[\w-]+", c["text"])}
        hit = len(terms & words)
        if hit:
            scored.append((hit, i))
    scored.sort(reverse=True)
    return [i for _, i in scored[:k]]


def main() -> int:
    t0 = time.perf_counter()
    chunks = load_chunks()
    print(f"{len(chunks)} chunks from {len(list((LAB/'corpus').glob('*.md')))}"
          f" documents")
    vectors = embed([c["text"] for c in chunks])
    print(f"embedded in {time.perf_counter() - t0:.1f}s, "
          f"dim {len(vectors[0])}\n")

    rec20, prec5, rows = [], [], []
    K = 5
    for q in GOLD:
        qv = embed([q.question])[0]
        ranked = sorted(range(len(chunks)),
                        key=lambda i: -cosine(qv, vectors[i]))
        gold = {tuple(s.split("::")) for s in q.gold_sections}

        def hits(idxs):
            return {(chunks[i]["doc_id"], chunks[i]["section"])
                    for i in idxs} & gold

        if not q.answerable:
            rows.append((q.qid, "unanswerable", "-", "-", ",".join(q.tags)))
            continue
        r5 = len(hits(ranked[:K])) / len(gold)
        # rank of the first gold chunk: varies continuously, unlike a
        # recall that saturates on a corpus this small
        rank = next((i + 1 for i, idx in enumerate(ranked)
                     if (chunks[idx]["doc_id"], chunks[idx]["section"])
                     in gold), None)
        kw_ranked = keyword_rank(chunks, q.question, len(chunks))
        kw_rank = next((i + 1 for i, idx in enumerate(kw_ranked)
                        if (chunks[idx]["doc_id"], chunks[idx]["section"])
                        in gold), None)
        rec20.append(r5)
        prec5.append(0)
        rows.append((q.qid, f"{r5:.2f}", str(rank or "-"),
                     str(kw_rank or "-"), ",".join(q.tags)))

    print(f"{'qid':<5}{'recall@5':>10}{'dense rank':>12}{'kw rank':>9}"
          f"  tags")
    for qid, a, b, c, tags in rows:
        print(f"{qid:<5}{a:>10}{b:>8}{c:>14}  {tags}")

    print(f"\n  mean recall@{K} {sum(rec20)/len(rec20):.2f}")
    zero = [r[0] for r in rows if r[1] == "0.00"]
    print(f"  questions with recall@{K} = 0: {zero or 'none'}")
    print("\n  dense beats keyword where the rank is lower, and vice versa.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
