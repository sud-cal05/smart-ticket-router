"""A/B test: static few-shot vs dynamic few-shot on the golden set. Runs the eval
twice (flag off, then on) and reports both accuracies. Run: python -m eval.ab_test
Costs a few cents. This is the evidence for 'why dynamic few-shot' — win or lose."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

GOLDEN = Path(__file__).parent / "golden.jsonl"


def load_golden() -> list[dict]:
    with open(GOLDEN) as f:
        return [json.loads(line) for line in f if line.strip()]


def run_eval(dynamic: bool) -> tuple[int, int, int]:
    # Set the flag BEFORE importing anything that reads it
    os.environ["ROUTER_DYNAMIC_FEWSHOT"] = "true" if dynamic else "false"
    # Force a fresh import of modules that captured the flag at import time
    for mod in ["router.settings", "router.core"]:
        sys.modules.pop(mod, None)
    # Clear cache so both runs actually hit the model
    import router.store as store
    from router.core import route_ticket
    from router.store import cache_get  # noqa: F401
    with store._connect() as conn:
        conn.execute("DELETE FROM cache")

    tickets = load_golden()
    cat_ok = pri_ok = 0
    for item in tickets:
        try:
            r = route_ticket(item["text"])
            cat_ok += r.category.value == item["category"]
            pri_ok += r.priority.value == item["priority"]
        except Exception:
            pass
    return cat_ok, pri_ok, len(tickets)


def main() -> None:
    print("Running STATIC few-shot...")
    s_cat, s_pri, n = run_eval(dynamic=False)
    print("Running DYNAMIC few-shot...")
    d_cat, d_pri, _ = run_eval(dynamic=True)

    print(f"\n{'='*50}")
    print(f"{'':20} {'Static':>10} {'Dynamic':>10}")
    print(f"{'Category accuracy':20} {s_cat}/{n:>8} {d_cat}/{n:>8}")
    print(f"{'Priority accuracy':20} {s_pri}/{n:>8} {d_pri}/{n:>8}")
    print(f"{'='*50}")
    winner = "dynamic" if (d_cat + d_pri) > (s_cat + s_pri) else "static"
    print(f"\nHigher combined accuracy: {winner.upper()}")
    print("(Small n — treat as directional, not definitive.)")


if __name__ == "__main__":
    main()