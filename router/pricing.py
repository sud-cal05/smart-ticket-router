"""Token→cost conversion. Prices are per 1M tokens and DO drift — verify current
rates at platform.openai.com/docs/pricing and update here. Isolated so pricing
changes touch exactly one file."""

# USD per 1,000,000 tokens. Update when OpenAI changes pricing.
_PRICES = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    rate = _PRICES.get(model, _PRICES["gpt-4o-mini"])
    return (
        prompt_tokens / 1_000_000 * rate["input"]
        + completion_tokens / 1_000_000 * rate["output"]
    )