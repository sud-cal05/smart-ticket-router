"""The core routing function. Pure and interface-agnostic: CLI, API, and batch mode
all call this. Reliability handling (retries, fallback) arrives in Phase 2."""

from router import llm
from router.prompt import build_system_prompt, build_user_prompt
from router.schema import RoutingResult

_SYSTEM_PROMPT = build_system_prompt()


def route_ticket(ticket_text: str) -> RoutingResult:
    """Classify a single support ticket into a validated RoutingResult."""
    user_prompt = build_user_prompt(ticket_text)
    return llm.classify(_SYSTEM_PROMPT, user_prompt)
