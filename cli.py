"""CLI for the ticket router.
  Single: python cli.py "ticket text"
  Batch:  python cli.py --batch input.csv output.csv   (input needs a 'text' column)
"""

import csv
import json
import sys

from dotenv import load_dotenv

load_dotenv()

from router.core import route_ticket  # noqa: E402
from router.guards import EmptyInputError  # noqa: E402


def run_single(text: str) -> None:
    try:
        result = route_ticket(text)
    except EmptyInputError as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)
    print(json.dumps(result.model_dump(), indent=2))


def run_batch(in_path: str, out_path: str) -> None:
    with open(in_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows or "text" not in rows[0]:
        print("Input CSV must have a 'text' column.")
        sys.exit(1)

    fields = ["text", "category", "priority", "assigned_team", "reasoning",
              "confidence", "fallback_used"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for i, row in enumerate(rows, 1):
            try:
                r = route_ticket(row["text"]).model_dump()
                writer.writerow({
                    "text": row["text"], "category": r["category"],
                    "priority": r["priority"], "assigned_team": r["assigned_team"],
                    "reasoning": r["reasoning"], "confidence": r["confidence"],
                    "fallback_used": r["fallback_used"],
                })
                print(f"[{i}/{len(rows)}] {r['category']}/{r['priority']}")
            except EmptyInputError:
                print(f"[{i}/{len(rows)}] skipped (empty)")
    print(f"\nDone -> {out_path}")


def main() -> None:
    if len(sys.argv) >= 4 and sys.argv[1] == "--batch":
        run_batch(sys.argv[2], sys.argv[3])
    elif len(sys.argv) >= 2:
        run_single(sys.argv[1])
    else:
        print('Usage:\n  python cli.py "ticket text"\n  python cli.py --batch in.csv out.csv')
        sys.exit(1)


if __name__ == "__main__":
    main()