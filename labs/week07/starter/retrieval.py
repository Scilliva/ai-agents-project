"""The embedding index and dense and keyword retrievers.

Chroma is a black box here, exactly as the syllabus asks. You put vectors in
with metadata and you get ranked ids out. What is worth your attention is
what you put in and how you score what comes back.

Two retrievers, because block 2 compares them:

  dense     embeddings, cosine similarity. Good at meaning, indifferent to
            exact strings.
  keyword   term overlap. The reverse. Deliberately crude, so it is obvious
            what it is doing.
"""

from __future__ import annotations

import json
import re
import urllib.request
import urllib.error

try:  # package import for the Week 6 integration; script import for the lab
    from .chunking import Chunk
except ImportError:
    from chunking import Chunk

from project.models import EMBED, OLLAMA_URL

EMBED_MODEL = EMBED.name


def embed(texts: list[str], batch: int = 32) -> list[list[float]]:
    """Embed a list of texts, in batches.

    One call per chunk is the obvious version and it is roughly thirty times
    slower on this corpus. The endpoint takes a list, so give it one.

    POST to f"{OLLAMA_URL}/api/embed" with a JSON body of
    {"model": EMBED_MODEL, "input": [...]} and read the "embeddings" key.
    """
    if batch <= 0:
        raise ValueError("batch must be positive")
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch):
        body = json.dumps({"model": EMBED_MODEL,
                           "input": texts[start:start + batch]}).encode()
        request = urllib.request.Request(
            f"{OLLAMA_URL}/api/embed", data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.loads(response.read())
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Could not reach Ollama embedding endpoint: {exc}") from exc
        vectors.extend(payload["embeddings"])
    return vectors


class DenseIndex:
    """Build once per configuration, then query it."""

    def __init__(self, chunks: list[Chunk], name: str = "run_a"):
        """Build the index.

        chromadb.EphemeralClient(), then get_or_create_collection(name),
        then add() with ids, embeddings, and metadatas carrying doc_id and
        section.

        Give the collection a NAME that encodes the configuration. Two
        chunkings have to be able to coexist during the block 3 sweep, and
        rebuilding without deleting is the classic way to end up with two
        chunkings in one index and numbers nobody can explain.

        Keep a dict from chunk_id to Chunk, because search has to map the
        ids Chroma returns back to objects. Set self.dim so the brief's
        conditions line has something to record.
        """
        import chromadb

        if not chunks:
            raise ValueError("cannot index an empty chunk list")
        self.by_id = {chunk.chunk_id: chunk for chunk in chunks}
        self.client = chromadb.EphemeralClient()
        self.collection = self.client.get_or_create_collection(name=name)
        vectors = embed([chunk.text for chunk in chunks])
        self.dim = len(vectors[0])
        self.collection.add(
            ids=[chunk.chunk_id for chunk in chunks], embeddings=vectors,
            metadatas=[{"doc_id": chunk.doc_id, "section": chunk.section}
                       for chunk in chunks],
        )

    def search(self, query: str, k: int = 20) -> list[Chunk]:
        """Embed the query, ask the collection, map ids back to Chunks."""
        if k <= 0:
            return []
        result = self.collection.query(
            query_embeddings=embed([query]), n_results=min(k, len(self.by_id)))
        ids = result["ids"][0]
        return [self.by_id[chunk_id] for chunk_id in ids]


def keyword_search(chunks: list[Chunk], query: str,
                   k: int = 20) -> list[Chunk]:
    """Term overlap. No model, no cost.

    Score each chunk by how many query terms appear in it, return the top k.
    Crude on purpose: in block 2 you will see a document that repeats a term
    in the wrong section outrank the section that answers the question.

    Break ties deterministically, by chunk_id, or two runs of your own code
    will disagree and you will spend ten minutes blaming the embedder.
    """
    if k <= 0:
        return []
    terms = set(re.findall(r"[\w-]+", query.casefold()))
    ranked = sorted(
        chunks,
        key=lambda chunk: (-len(terms & set(re.findall(
            r"[\w-]+", chunk.text.casefold()))), chunk.chunk_id),
    )
    return ranked[:k]
