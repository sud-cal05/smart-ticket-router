"""OpenAI adapter. The ONLY module aware of the provider. Uses strict structured
outputs so the model can only emit schema-conforming JSON; we still re-validate with
Pydantic afterward as defense in depth."""

import json
import os

from openai import APIError, APITimeoutError, OpenAI, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from router.schema import RoutingResult

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def _strict_schema() -> dict:
    """Pydantic's schema, adjusted for OpenAI strict mode:
    - every property must be listed in 'required'
    - additionalProperties must be false (at every object level)
    - inline all $ref enums (strict mode dislikes $ref + sibling keywords)
    - strip 'default' keywords (strict mode forbids them)
    """
    schema = RoutingResult.model_json_schema()
    defs = schema.pop("$defs", {})

    def resolve(node):
        if isinstance(node, dict):
            # Inline any $ref by replacing the node with the referenced definition
            if "$ref" in node:
                ref_name = node["$ref"].split("/")[-1]
                return resolve(dict(defs[ref_name]))
            # Strip forbidden 'default' keyword
            node.pop("default", None)
            # Recurse into children
            resolved = {k: resolve(v) for k, v in node.items()}
            # Enforce strict object rules
            if resolved.get("type") == "object" and "properties" in resolved:
                resolved["required"] = list(resolved["properties"].keys())
                resolved["additionalProperties"] = False
            return resolved
        if isinstance(node, list):
            return [resolve(item) for item in node]
        return node

    return resolve(schema)


@retry(
    retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _call_api(client, model, temperature, messages):
    """Returns (raw_content, usage_dict). AuthenticationError is not retried."""
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "routing_result",
                "strict": True,
                "schema": _strict_schema(),
            },
        },
    )
    usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "model": model,
    }
    return response.choices[0].message.content, usage


def classify(system_prompt: str, user_prompt: str) -> tuple[RoutingResult, dict]:
    """Returns (result, usage). usage carries token counts + model for cost logging."""
    client = _get_client()
    model = os.environ.get("ROUTER_MODEL", "gpt-4o-mini")
    temperature = float(os.environ.get("ROUTER_TEMPERATURE", "0"))
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    raw, usage = _call_api(client, model, temperature, messages)
    try:
        return RoutingResult.model_validate(json.loads(raw)), usage
    except Exception as e:
        messages.append({"role": "assistant", "content": raw})
        messages.append({
            "role": "user",
            "content": f"Your previous output failed validation: {e}. "
                       f"Return ONLY corrected JSON matching the schema.",
        })
        raw, usage = _call_api(client, model, temperature, messages)
        return RoutingResult.model_validate(json.loads(raw)), usage
