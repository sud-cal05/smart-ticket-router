"""Feature flags for optional differentiators. All OFF by default so the baseline
behavior (and the existing test suite) is unchanged unless explicitly enabled."""

import os


def _flag(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).lower() in ("1", "true", "yes")


DYNAMIC_FEWSHOT = _flag("ROUTER_DYNAMIC_FEWSHOT", "true")
TIERED_ESCALATION = _flag("ROUTER_TIERED_ESCALATION")

# Escalation config
ESCALATION_THRESHOLD = float(os.environ.get("ROUTER_ESCALATION_THRESHOLD", "0.6"))
STRONG_MODEL = os.environ.get("ROUTER_STRONG_MODEL", "gpt-4o")