"""Phase 2 reliability tests. Every failure mode is mocked — no real API calls.
Proves the ladder never crashes and each rung behaves."""

from unittest.mock import patch

import pytest

from router.guards import EmptyInputError, prepare, redact_pii, truncate, validate
from router.schema import Priority, RoutingResult


def _ok() -> RoutingResult:
    return RoutingResult(
        category="billing", priority=Priority.high, assigned_team="Finance Ops",
        reasoning="x", confidence=0.9,
    )


def test_empty_input_rejected_before_api():
    with pytest.raises(EmptyInputError):
        validate("   ")


def test_truncate_keeps_head_and_tail():
    long = "A" * 5000 + "B" * 5000
    out = truncate(long)
    assert len(out) < len(long)
    assert out.startswith("A") and out.endswith("B")
    assert "TRUNCATED" in out


def test_pii_redaction():
    text = "email me at john@example.com or call +1 415 555 1234"
    red = redact_pii(text)
    assert "john@example.com" not in red
    assert "[EMAIL]" in red
    assert "[PHONE]" in red


def test_api_failure_falls_back_no_crash():
    with patch("router.core.llm.classify", side_effect=RuntimeError("API down")):
        from router.core import route_ticket
        result = route_ticket("I was charged twice")
    assert result.fallback_used is True
    assert result.confidence <= 0.3
    assert result.category  # still a valid category


def test_successful_result_is_cached(tmp_path, monkeypatch):
    # Isolate the cache in a temp DB so the test starts from a clean slate
    # and never touches the real data/router.db.
    import router.store as store

    test_db = tmp_path / "test_cache.db"
    monkeypatch.setattr(store, "_DB_PATH", test_db)
    store.init_db()

    from router.core import _hash, route_ticket

    unique = "please add dark mode number 84213"
    with patch("router.core.llm.classify", return_value=_ok()) as m:
        route_ticket(unique)  # first call -> hits LLM, caches
        route_ticket(unique)  # second call -> should hit cache
    assert m.call_count == 1  # LLM called only once
    assert store.cache_get(_hash(prepare(unique))) is not None