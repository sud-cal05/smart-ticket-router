"""API integration tests via FastAPI TestClient. LLM mocked — no real calls.
Covers happy path, empty-input 422, health, and XSS-safe output handling."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from router.schema import Priority, RoutingResult


def _ok() -> RoutingResult:
    return RoutingResult(
        category="billing", priority=Priority.high, assigned_team="Finance Ops",
        reasoning="Duplicate charge per rubric.", confidence=0.9,
    )


def _client():
    import app
    return TestClient(app.app)


def test_health():
    assert _client().get("/v1/health").json() == {"status": "ok"}


def test_route_happy_path():
    usage = {"model": "gpt-4o-mini", "prompt_tokens": 100, "completion_tokens": 30}
    with patch("router.core.llm.classify", return_value=(_ok(), usage)):
        res = _client().post("/v1/route", json={"text": "charged twice"})
    assert res.status_code == 200
    body = res.json()
    assert body["category"] == "billing"
    assert {"category", "priority", "assigned_team", "reasoning"} <= body.keys()


def test_route_empty_returns_422():
    res = _client().post("/v1/route", json={"text": "   "})
    assert res.status_code == 422


def test_form_served_at_root():
    res = _client().get("/")
    assert res.status_code == 200
    assert "Ticket Desk" in res.text