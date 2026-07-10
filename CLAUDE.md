# Smart Ticket Router
Python 3.11 · FastAPI · Pydantic · pytest · ruff · Docker

## Commands
- make test   # unit tests, mocked LLM — run after EVERY change
- make eval   # live golden eval (~$0.02) — only when I explicitly ask
- make lint   # ruff check

## Rules
- Never call the real OpenAI API in unit tests; mock the adapter.
- Never touch .env; never print or log the API key.
- All responses must satisfy router/schema.py (added in Phase 1) — it is the contract.
- Golden dataset (eval/) is append-only.
- Small, single-purpose changes; I commit manually with my own messages.