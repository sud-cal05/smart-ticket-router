"""The core routing function. Descends the reliability ladder:
guards -> cache -> LLM (with retry+repair) -> keyword fallback. Never raises to the
caller except EmptyInputError; everything else degrades to a fallback result."""

import hashlib

from router import llm
from router.fallback import keyword_route
from router.guards import prepare
from router.prompt import build_system_prompt, build_user_prompt
from router.schema import RoutingResult
from router.store import cache_get, cache_set

_SYSTEM_PROMPT = build_system_prompt()


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def route_ticket(ticket_text: str) -> RoutingResult:
    """Route one ticket through the full reliability ladder."""
    # Rung 1: guards (EmptyInputError intentionally propagates to the caller)
    clean = prepare(ticket_text)

    # Rung 2: cache
    key = _hash(clean)
    cached = cache_get(key)
    if cached is not None:
        return RoutingResult.model_validate(cached)

    # Rung 3-4: LLM with retry + repair
    try:
        result = llm.classify(_SYSTEM_PROMPT, build_user_prompt(clean))
        cache_set(key, result.model_dump())
        return result
    except Exception:
        # Rung 5: deterministic fallback — never crash
        return keyword_route(clean)