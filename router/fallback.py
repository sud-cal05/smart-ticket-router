"""Deterministic keyword fallback. Used only when the LLM is unavailable, so the
system degrades gracefully instead of crashing. Driven by the same taxonomy.yaml."""

from router.config import TAXONOMY
from router.schema import Priority, RoutingResult


def keyword_route(text: str) -> RoutingResult:
    """Best-effort classification by keyword match. Always flagged as fallback."""
    lowered = text.lower()
    best_category = "general_inquiry"
    best_hits = 0

    for name, cat in TAXONOMY["categories"].items():
        hits = sum(1 for kw in cat["keywords"] if str(kw).lower() in lowered)
        if hits > best_hits:
            best_hits, best_category = hits, name

    team = TAXONOMY["categories"][best_category]["team"]
    return RoutingResult(
        category=best_category,
        priority=Priority.medium,  # conservative default when uncertain
        assigned_team=team,
        reasoning="AI unavailable — provisional keyword-based routing; queued for human review.",
        confidence=0.3,
        needs_clarification=True,
        clarifying_question="Routing was degraded; please confirm this ticket's category.",
        fallback_used=True,
    )