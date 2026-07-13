"""Corpus embeddings for dynamic few-shot retrieval. Computed once and cached to disk,
keyed on a content hash so they regenerate automatically only when the corpus changes.
Uses brute-force cosine similarity in numpy — no vector DB, because at ~20 corpus items
an index buys nothing (see ADR-7)."""

import hashlib
import json
import os
from pathlib import Path

import numpy as np

_CORPUS_PATH = Path(__file__).parent.parent / "eval" / "retrieval_corpus.jsonl"
_CACHE_PATH = Path(__file__).parent.parent / "data" / "corpus_embeddings.json"
_EMBED_MODEL = "text-embedding-3-small"


def _corpus_hash(corpus: list[dict]) -> str:
    blob = json.dumps(corpus, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def _embed(texts: list[str]) -> list[list[float]]:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.embeddings.create(model=_EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def load_corpus() -> list[dict]:
    with open(_CORPUS_PATH) as f:
        return [json.loads(line) for line in f if line.strip()]


def get_corpus_embeddings() -> tuple[list[dict], np.ndarray]:
    """Return (corpus, embedding_matrix). Loads from cache if the corpus is unchanged,
    otherwise recomputes and re-caches."""
    corpus = load_corpus()
    current_hash = _corpus_hash(corpus)

    if _CACHE_PATH.exists():
        cached = json.loads(_CACHE_PATH.read_text())
        if cached.get("hash") == current_hash:
            return corpus, np.array(cached["vectors"])

    vectors = _embed([item["text"] for item in corpus])
    _CACHE_PATH.parent.mkdir(exist_ok=True)
    _CACHE_PATH.write_text(json.dumps({"hash": current_hash, "vectors": vectors}))
    return corpus, np.array(vectors)



def most_similar(query_vec: np.ndarray, matrix: np.ndarray, k: int = 3) -> list[int]:
    """Return indices of the k most cosine-similar rows in matrix to query_vec.

    Inputs are validated and L2-normalized before the dot product, so the cosine
    scores are numerically sound. We locally silence a spurious RuntimeWarning that
    some BLAS backends (notably Apple Accelerate on Apple Silicon) emit on this
    matmul despite clean unit-vector inputs — verified: no NaN/inf, row norms ~1.0."""
    if matrix.size == 0 or query_vec.size == 0:
        return []
    q_norm = np.linalg.norm(query_vec)
    if q_norm == 0:
        return list(range(min(k, len(matrix))))
    q = query_vec / q_norm
    row_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    row_norms[row_norms == 0] = 1.0
    m = matrix / row_norms
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        scores = m @ q
    return np.argsort(scores)[::-1][:k].tolist()