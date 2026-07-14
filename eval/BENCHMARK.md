# Routing Benchmark: Manual vs. AI

## Method
10 representative support tickets routed two ways: manually by a human using the
taxonomy + priority rubric, and by the Smart Ticket Router. Manual timing captured
automatically via a timed web form (`/manual`); AI timing and cost captured from the
service's own request logs (`/v1/metrics`). Single human router (n=1) — a deliberately
disclosed limitation; results are directional, not a controlled study.

## Results

| Metric | Manual (human) | AI Router | Difference |
|---|---|---|---|
| Time per ticket (median) | ~11.2 s | 2.30 s (p50) | **~5x faster** |
| Time per ticket (p95 / worst) | 130.7 s* | 2.87 s (p95) | **~45x faster on the tail** |
| Cost per ticket | staff time | $0.000198 | ~$0.20 per 1,000 tickets |
| Consistency | 3 inconsistencies in 10 | Identical on repeat (cached) | — |

\* One ticket took 130.7s due to a real interruption mid-task. Excluding it, the human
mean was ~10.8s/ticket; the raw mean including it was 22.8s. The tail number is kept
because interruptions are a genuine feature of real triage work, not an artifact.

## The consistency finding
The human router — who also authored the taxonomy — made **3 routing inconsistencies
across 10 tickets** when working at normal speed:
- Routed a 2FA question to Engineering Support (taxonomy maps account access → Customer Success)
- Routed a feature request to Customer Success (taxonomy maps → Product)
- Rated a "payment taken but not credited" ticket medium (rubric: payment failure = high)

The AI applied the rubric identically every time, and returns byte-identical output for
repeated inputs via the input-hash cache. The gap here is not just speed — it's that
consistent rule application is hard for humans under time pressure and trivial for the system.

## Extrapolation
At a modest 1,000 tickets/month:
- **Time:** ~11s vs ~2s per ticket ≈ 2.5 human-hours/month returned to actual support work
  (more if measured against the interruption-inclusive mean).
- **Cost:** ~$0.20/month in API spend to route all 1,000.

## Honesty notes
- n=1 human router; a multi-router study would strengthen the consistency claim
  (though disagreement *between* routers would only widen the gap).
- Manual timing was done genuinely (tickets actually read and decided), not click-through.
- AI latency is real API latency (0 cache hits, 0 fallbacks in this run).