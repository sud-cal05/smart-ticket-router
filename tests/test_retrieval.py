"""Tests for retrieval math. Cosine similarity is tested against known vectors —
no embedding API calls needed, so this stays free and offline."""

import numpy as np

from router.embeddings import most_similar


def test_most_similar_finds_identical_vector():
    matrix = np.array([[1.0, 0.0], [0.0, 1.0], [0.9, 0.1]])
    query = np.array([1.0, 0.0])
    top = most_similar(query, matrix, k=1)
    assert top[0] == 0  # exact match is most similar


def test_most_similar_ranks_by_direction_not_magnitude():
    matrix = np.array([[10.0, 0.0], [0.0, 5.0]])
    query = np.array([1.0, 0.0])  # same direction as row 0, tiny magnitude
    top = most_similar(query, matrix, k=2)
    assert top[0] == 0  # cosine ignores magnitude — direction match wins


def test_returns_k_indices():
    matrix = np.random.rand(10, 8)
    query = np.random.rand(8)
    assert len(most_similar(query, matrix, k=3)) == 3