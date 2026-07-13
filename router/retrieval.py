"""Dynamic few-shot: embed the incoming ticket and retrieve the k most similar labeled
tickets from the corpus to use as in-context examples."""

import os

import numpy as np

from router.embeddings import get_corpus_embeddings, most_similar

_corpus = None
_matrix = None


def _ensure_loaded():
    global _corpus, _matrix
    if _corpus is None:
        _corpus, _matrix = get_corpus_embeddings()


def _embed_query(text: str) -> np.ndarray:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.embeddings.create(model="text-embedding-3-small", input=[text])
    return np.array(resp.data[0].embedding)


def retrieve_examples(ticket_text: str, k: int = 3) -> list[dict]:
    """Return the k most semantically similar corpus tickets as example dicts."""
    _ensure_loaded()
    query_vec = _embed_query(ticket_text)
    idxs = most_similar(query_vec, _matrix, k)
    return [_corpus[i] for i in idxs]


def format_examples(examples: list[dict]) -> str:
    """Render retrieved examples as a prompt-ready block."""
    lines = ["Here are similar past tickets and how they were routed:"]
    for ex in examples:
        lines.append(f'- "{ex["text"]}" -> category: {ex["category"]}, priority: {ex["priority"]}')
    return "\n".join(lines)