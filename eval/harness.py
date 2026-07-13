"""Golden-set evaluation harness. Routes every labeled ticket, compares to expected
category/priority, prints per-dimension accuracy and every mismatch.
Run: python -m eval.harness   (costs ~2-3 cents for 25 tickets)"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from router.core import route_ticket  # noqa: E402
from router.guards import EmptyInputError  # noqa: E402

GOLDEN = Path(__file__).parent / "golden.jsonl"


def load_golden() -> list[dict]:
    with open(GOLDEN) as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    tickets = load_golden()
    cat_correct = pri_correct = valid = 0
    mismatches = []

    for i, item in enumerate(tickets, 1):
        try:
            result = route_ticket(item["text"])
            valid += 1
            cat_ok = result.category.value == item["category"]
            pri_ok = result.priority.value == item["priority"]
            cat_correct += cat_ok
            pri_correct += pri_ok
            if not (cat_ok and pri_ok):
                mismatches.append(
                    f"[{i:2}] {item['text'][:50]!r}\n"
                    f"      expected: {item['category']}/{item['priority']}  "
                    f"got: {result.category}/{result.priority.value}"
                )
        except EmptyInputError:
            valid += 1  # rejecting empty input is correct behavior
        except Exception as e:
            mismatches.append(f"[{i:2}] ERROR {type(e).__name__}: {e}")

    n = len(tickets)
    print(f"\n{'='*55}")
    print(f"Tickets:            {n}")
    print(f"Valid responses:    {valid}/{n}")
    print(f"Category accuracy:  {cat_correct}/{n}  ({100*cat_correct/n:.0f}%)")
    print(f"Priority accuracy:  {pri_correct}/{n}  ({100*pri_correct/n:.0f}%)")
    print(f"{'='*55}")
    if mismatches:
        print("\nMismatches (review these — some may be YOUR label, not a bug):\n")
        print("\n\n".join(mismatches))
    else:
        print("\nPerfect run.")


if __name__ == "__main__":
    main()