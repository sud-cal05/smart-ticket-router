"""Shared pytest fixtures. Auto-isolates the SQLite store AND the embedding API for
every test, so no test touches the real data/router.db, sees another test's cached
rows, or makes a network call. All autouse — applies to every test automatically."""

import pytest


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Point the store at a fresh temp DB per test. Restored automatically after."""
    import router.store as store

    monkeypatch.setattr(store, "_DB_PATH", tmp_path / "test.db")
    store.init_db()
    yield


@pytest.fixture(autouse=True)
def no_real_embeddings(monkeypatch):
    """Stub retrieval so tests never hit the embedding API."""
    def _no_examples(*args, **kwargs):
        return []
    monkeypatch.setattr("router.retrieval.retrieve_examples", _no_examples, raising=False)