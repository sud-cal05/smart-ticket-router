# Ticket Desk

An LLM-powered support ticket router. Paste any support message and it returns a
structured routing decision — **category, priority, assigned team, and one-line
reasoning** — as validated JSON, in about two seconds.

Built to be reliable (never crashes, always returns valid JSON), cheap (~$0.20 per
1,000 tickets), and honest about where it's uncertain (flags vague tickets for human
review instead of guessing).

---

## Quick start

Requires Python 3.11+ and an OpenAI API key.

```bash
git clone <your-repo-url>
cd <repo>
python3.11 -m venv .venv && source .venv/bin/activate
make install
cp .env.example .env          # then edit .env and add your OPENAI_API_KEY
make test                     # 27 tests, no API calls — should all pass
```

Route your first ticket:

```bash
python cli.py "I was charged twice and can't get a refund"
```

Or run the web interface:

```bash
make run                      # then open http://localhost:8000
```

### Docker (alternative — fully reproducible environment)

```bash
docker build -t ticket-desk .
docker run --rm --env-file .env -p 8000:8000 ticket-desk
```

---

## What you get

Every response is validated JSON with a guaranteed shape:

```json
{
  "category": "billing",
  "priority": "high",
  "assigned_team": "Finance Ops",
  "reasoning": "User reports a duplicate charge — a payment failure per the rubric.",
  "confidence": 0.9,
  "needs_clarification": false,
  "sentiment": "neutral",
  "fallback_used": false
}
```

The four required fields (`category`, `priority`, `assigned_team`, `reasoning`) are
always present and enum-constrained — an invalid category or priority is structurally
impossible, not just unlikely.

---

## Interfaces

- **Web form** — `http://localhost:8000` — for non-technical users; shows a filed-record
  card, priority-colored, with a visible banner when routing is degraded.
- **REST API** — `POST /v1/route`, plus `/v1/health`, `/v1/metrics`, and auto-generated
  docs at `/docs`.
- **CLI** — `python cli.py "text"` for one ticket, or
  `python cli.py --batch in.csv out.csv` to route a whole queue (input needs a `text` column).

---

## How it works

```
                          ┌──────────────────────────────────────────────┐
  Web form ──┐            │                Router Service                │
  CLI ───────┼──▶ FastAPI │  1 Input guards (empty / length / PII mask)  │
  Batch CSV ─┘   /v1/route│  2 Cache lookup (hash of normalized input)   │
                          │  3 Dynamic few-shot retrieval (top-3 similar) │
                          │  4 LLM ── strict structured JSON output       │
                          │       retry+backoff · one-shot repair         │
                          │  5 Tiered escalation (low-confidence tail)    │
                          │  6 Fallback: keyword classifier → human review│
                          │  7 Log: SQLite (latency, tokens, cost)        │
                          └──────────────────────────────────────────────┘
        taxonomy.yaml — categories, teams, priority rubric, keywords
```

A request descends a **reliability ladder** — each rung degrades gracefully to the next,
so the system never crashes:

1. **Guards** reject empty input before spending a token; over-long input is truncated;
   emails/phone numbers are redacted before anything leaves the machine.
2. **Cache** returns byte-identical results for repeat inputs (an input-hash lookup) —
   this is what guarantees consistency despite LLM non-determinism.
3. **Dynamic few-shot** retrieves the 3 most semantically similar labeled tickets and
   shows them to the model as examples (falls back to static examples if unavailable).
4. **Strict structured output** constrains generation so the model can only emit
   schema-conforming JSON; the result is re-validated with Pydantic as defense in depth.
5. **Tiered escalation** re-runs low-confidence but substantive tickets on a stronger
   model — the ~85% of easy tickets stay cheap; only the uncertain tail pays more.
6. **Keyword fallback** provides best-effort routing (flagged for human review) if the
   API is entirely unavailable — the system degrades instead of dying.

Design decisions and trade-offs (model choice, retrieval approach, deployment,
storage) are covered in `LEARNINGS.md` and the codebase comments.

---

## Results

Measured on this repo. Small samples — treated as directional, not definitive.

| Metric | Result | Notes |
|---|---|---|
| **Routing accuracy** | 96% category, 96% priority | 25-ticket labeled golden set |
| **Speed** | ~2.3s (AI) vs ~11s (manual) | AI p50 latency vs human median |
| **Cost** | ~$0.20 per 1,000 tickets | `gpt-4o-mini` default tier |
| **Escalation cost delta** | 17x | strong model ($0.0035) vs mini ($0.0002) per ticket |
| **Consistency** | identical output on repeat | via input-hash cache |

A notable finding: the human router (who also authored the taxonomy) made **3 routing
inconsistencies across 10 tickets** under time pressure, while the system applies the
rubric identically every time. The value is not just speed — it's consistent rule
application. Full method and caveats in [`eval/BENCHMARK.md`](eval/BENCHMARK.md).

---

## Configuration

Set in `.env` (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | — | Required. Kept server-side; never sent to the browser. |
| `ROUTER_MODEL` | `gpt-4o-mini` | Default (cheap) model. |
| `ROUTER_DYNAMIC_FEWSHOT` | `true` | Retrieve similar examples per request. |
| `ROUTER_TIERED_ESCALATION` | `false` | Escalate low-confidence tickets to a stronger model. |
| `ROUTER_ESCALATION_THRESHOLD` | `0.6` | Confidence below which escalation may fire. |
| `ROUTER_STRONG_MODEL` | `gpt-4o` | Model used when escalating. |

The routing taxonomy (categories, teams, priority rubric, fallback keywords) lives in
`taxonomy.yaml` — change routing behavior by editing that file, not the code.

---

## Testing

```bash
make test                 # 27 unit/integration tests — LLM mocked, no API calls, free
make lint                 # ruff
python -m eval.harness    # live accuracy eval on the golden set (~2 cents)
python -m eval.ab_test    # static vs dynamic few-shot comparison (~a few cents)
```

Tests never hit the real API (the adapter is mocked and each test gets an isolated
database), so they're free and safe to run in CI on every push.

---

## Known limitations

- **Small evaluation set** (25 tickets). Accuracy figures are directional; a larger
  labeled set would tighten them.
- **Non-determinism.** `temperature=0` reduces but does not eliminate output variance;
  the cache neutralizes it for repeat inputs, but two distinct-but-similar tickets may
  route slightly differently.
- **Taxonomy is fixed at config time.** New categories require editing `taxonomy.yaml`;
  the model won't invent categories outside it (by design).
- **Single-node.** SQLite and in-memory retrieval suit demo/small-team scale; the
  documented path to Postgres + a shared cache is in `docs/PLAN.md`.

---

## Scaling

The service is stateless, so it scales horizontally behind a load balancer. SQLite →
Postgres is a connection-string change (the schema is already relational). At ~thousands
of corpus examples, the in-memory cosine similarity would move to a vector index. None of
this is built — it's documented as the deliberate next step rather than over-engineered now.

## License

MIT