"""Command-line interface for routing a single ticket.
Usage: python cli.py "my ticket text here"
"""

import json
import sys

from dotenv import load_dotenv

load_dotenv()  # read .env before importing anything that needs the key

from router.core import route_ticket  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python cli.py "ticket text"')
        sys.exit(1)

    ticket_text = sys.argv[1]
    result = route_ticket(ticket_text)
    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()
