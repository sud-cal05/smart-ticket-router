"""Tiered escalation logic tests. Both models mocked — verifies WHEN escalation
fires (low confidence + substantive) and when it's correctly skipped (vague ticket)."""

from unittest.mock import patch

from router.schema import Priority, RoutingResult


def _result(confidence: float, needs_clarification: bool = False) -> RoutingResult:
    return RoutingResult(
        category="technical_issue", priority=Priority.medium,
        assigned_team="Engineering Support", reasoning="x",
        confidence=confidence, needs_clarification=needs_clarification,
    )


def _usage(model="gpt-4o-mini"):
    return {"model": model, "prompt_tokens": 100, "completion_tokens": 30}


def test_escalates_on_low_confidence_substantive(monkeypatch):
    monkeypatch.setattr("router.settings.TIERED_ESCALATION", True)
    monkeypatch.setattr("router.settings.ESCALATION_THRESHOLD", 0.6)

    # cheap model returns low confidence; strong model returns high
    calls = [(_result(0.4), _usage("gpt-4o-mini")),
             (_result(0.95), _usage("gpt-4o"))]
    with patch("router.core.llm.classify", side_effect=calls) as m:
        from router.core import route_ticket
        result = route_ticket("the reports page keeps throwing an odd error sometimes")
    assert m.call_count == 2               # escalated
    assert result.confidence == 0.95       # got the strong-model result


def test_skips_escalation_when_needs_clarification(monkeypatch):
    monkeypatch.setattr("router.settings.TIERED_ESCALATION", True)
    monkeypatch.setattr("router.settings.ESCALATION_THRESHOLD", 0.6)

    # cheap model is unsure AND flags for clarification -> must NOT escalate
    calls = [(_result(0.3, needs_clarification=True), _usage("gpt-4o-mini"))]
    with patch("router.core.llm.classify", side_effect=calls) as m:
        from router.core import route_ticket
        route_ticket("broken")
    assert m.call_count == 1               # did NOT escalate — saved the money


def test_no_escalation_when_confident(monkeypatch):
    monkeypatch.setattr("router.settings.TIERED_ESCALATION", True)
    with patch("router.core.llm.classify",
               side_effect=[(_result(0.9), _usage())]) as m:
        from router.core import route_ticket
        route_ticket("I was charged twice and want a refund")
    assert m.call_count == 1               # confident -> no escalation