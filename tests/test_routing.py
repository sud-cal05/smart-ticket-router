"""Unit tests for the routing layer. The LLM is mocked — these never call OpenAI,
so they're free, deterministic, and safe to run in CI on every push."""

from unittest.mock import patch

from router.config import CATEGORY_NAMES, TAXONOMY
from router.prompt import build_system_prompt, build_user_prompt
from router.schema import Priority, RoutingResult


def _fake_result() -> RoutingResult:
    return RoutingResult(
        category="billing",
        priority=Priority.high,
        assigned_team="Finance Ops",
        reasoning="User reports a duplicate charge — money movement failure per rubric.",
        confidence=0.92,
    )


def test_taxonomy_categories_map_to_valid_teams():
    valid = set(TAXONOMY["teams"])
    for name, cat in TAXONOMY["categories"].items():
        assert cat["team"] in valid, f"{name} -> unknown team"


def test_schema_rejects_bad_priority():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        RoutingResult(
            category="billing",
            priority="urgent",  # not in enum
            assigned_team="Finance Ops",
            reasoning="x",
            confidence=0.5,
        )


def test_system_prompt_contains_all_categories():
    prompt = build_system_prompt()
    for name in CATEGORY_NAMES:
        assert name in prompt


def test_user_prompt_wraps_ticket_in_delimiters():
    up = build_user_prompt("help me")
    assert "<ticket>" in up and "</ticket>" in up and "help me" in up


def test_route_ticket_returns_validated_result():
    # Patch the adapter so no real API call happens.
    with patch("router.core.llm.classify", return_value=_fake_result()):
        from router.core import route_ticket

        result = route_ticket("I was charged twice!")
    assert result.category == "billing"
    assert result.priority == Priority.high
    assert result.assigned_team == "Finance Ops"
    assert 0.0 <= result.confidence <= 1.0
