"""Phase 1 exit gate: route 10 varied tickets, assert every response is valid JSON
with all four required fields. Costs ~1 cent. Run: python -m eval.smoke"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from router.core import route_ticket  # noqa: E402

TICKETS = [
    "I was charged twice for my subscription this month.",
    "The app crashes every time I try to upload a photo.",
    "I can't log in even after resetting my password three times.",
    "Can you please add a dark mode to the mobile app?",
    "What are your customer support hours?",
    "I think someone hacked my account — there's a login from another country.",
    "Payment failed but money was deducted from my bank.",
    "The dashboard loads really slowly since yesterday's update.",
    "How do I export my data to CSV?",
    "My invoice shows the wrong billing address.",
]

REQUIRED = {"category", "priority", "assigned_team", "reasoning"}


def main() -> None:
    passed = 0
    for i, ticket in enumerate(TICKETS, 1):
        try:
            result = route_ticket(ticket).model_dump()
            missing = REQUIRED - result.keys()
            assert not missing, f"missing fields: {missing}"
            # round-trip through JSON to prove it's serializable/parseable
            json.loads(json.dumps(result))
            passed += 1
            print(f"[{i:2}/10] OK   {result['category']:16} {result['priority']:6} "
                  f"| {ticket[:45]}")
        except Exception as e:
            print(f"[{i:2}/10] FAIL {type(e).__name__}: {e} | {ticket[:45]}")

    verdict = "PASS — exit gate met." if passed == 10 else "FAIL — investigate above."
    print(f"\n{passed}/10 valid. {verdict}")


if __name__ == "__main__":
    main()