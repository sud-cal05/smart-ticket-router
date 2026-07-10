# Smart Ticket Router

Reads any support message and returns `category`, `priority`, `assigned_team`,
and one-line `reasoning` as validated JSON.

## Status
Phase 0 — scaffold. Routing logic lands in Phase 1.

## Setup (Option A — local)
```bash
git clone <your-repo-url>
cd smart-ticket-router
python3.11 -m venv .venv && source .venv/bin/activate
make install
cp .env.example .env   # then add your real OPENAI_API_KEY
make test
```

## Setup (Option B — Docker)
```bash
docker build -t smart-ticket-router .
docker run --rm --env-file .env -p 8000:8000 smart-ticket-router
```

## Commands
- `make test` — run unit tests (no API calls, free)
- `make lint` — ruff check
- `make run` — start the API locally

## License
MIT