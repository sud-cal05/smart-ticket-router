"""Core routing with reliability ladder + per-request logging (latency, tokens, cost)."""

import hashlib
import time

from router import llm, settings
from router.fallback import keyword_route
from router.guards import prepare
from router.pricing import estimate_cost
from router.prompt import build_system_prompt, build_user_prompt
from router.schema import RoutingResult
from router.store import cache_get, cache_set, log_request

_SYSTEM_PROMPT = build_system_prompt()


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def route_ticket(ticket_text: str) -> RoutingResult:
    """Route one ticket through the reliability ladder; log metrics for every call."""
    clean = prepare(ticket_text)  # EmptyInputError propagates
    key = _hash(clean)
    start = time.perf_counter()

    cached = cache_get(key)
    if cached is not None:
        result = RoutingResult.model_validate(cached)
        _log(key, result, start, cache_hit=True)
        return result

    try:
        examples_block = ""
        if settings.DYNAMIC_FEWSHOT:
            try:
                from router.retrieval import format_examples, retrieve_examples
                examples_block = format_examples(retrieve_examples(clean))
            except Exception:
                # embedding failed -> fall back to static few-shot, still use the LLM
                examples_block = ""

        user_prompt = build_user_prompt(clean, examples_block)
        result, usage = llm.classify(_SYSTEM_PROMPT, user_prompt)
        _log(key, result, start, usage=usage)  # log the cheap-model attempt

        # Tiered escalation: re-run on the strong model ONLY when the cheap model was
        # uncertain AND the ticket is substantive. Vague tickets that need clarification
        # won't benefit from a bigger model, so we don't spend on them.
        if (
            settings.TIERED_ESCALATION
            and result.confidence < settings.ESCALATION_THRESHOLD
            and not result.needs_clarification
        ):
            esc_start = time.perf_counter()
            result, usage = llm.classify(_SYSTEM_PROMPT, user_prompt, model=settings.STRONG_MODEL)
            _log(key, result, esc_start, usage=usage)  # log the escalated attempt too

        cache_set(key, result.model_dump())
        return result
    except Exception:
        result = keyword_route(clean)
        _log(key, result, start, fallback=True)
        return result


def _log(key, result, start, usage=None, cache_hit=False, fallback=False):
    latency_ms = (time.perf_counter() - start) * 1000
    usage = usage or {}
    cost = 0.0
    if usage:
        cost = estimate_cost(
            usage["model"], usage["prompt_tokens"], usage["completion_tokens"]
        )
    log_request({
        "input_hash": key,
        "category": result.category.value,
        "priority": result.priority.value,
        "confidence": result.confidence,
        "latency_ms": latency_ms,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "cost_usd": cost,
        "model": usage.get("model", "cache" if cache_hit else "fallback"),
        "cache_hit": int(cache_hit),
        "fallback_used": int(fallback),
    })