"""Minimal SQLite persistence. Phase 2 uses it only for the response cache;
Phase 5 extends the same file with full request logging. Single file, zero-ops."""

import json
import sqlite3
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent / "data" / "router.db"


def _connect() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")  # safer under concurrent access
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS cache (
                input_hash TEXT PRIMARY KEY,
                result_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_hash TEXT,
                category TEXT,
                priority TEXT,
                confidence REAL,
                latency_ms REAL,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                cost_usd REAL,
                model TEXT,
                cache_hit INTEGER DEFAULT 0,
                fallback_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )


def cache_get(input_hash: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT result_json FROM cache WHERE input_hash = ?", (input_hash,)
        ).fetchone()
    return json.loads(row[0]) if row else None


def cache_set(input_hash: str, result: dict) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cache (input_hash, result_json) VALUES (?, ?)",
            (input_hash, json.dumps(result)),
        )


def log_request(row: dict) -> None:
    with _connect() as conn:
        conn.execute(
            """INSERT INTO requests
               (input_hash, category, priority, confidence, latency_ms, prompt_tokens,
                completion_tokens, cost_usd, model, cache_hit, fallback_used)
               VALUES (:input_hash, :category, :priority, :confidence, :latency_ms, :prompt_tokens,
                       :completion_tokens, :cost_usd, :model, :cache_hit, :fallback_used)""",
            row,
        )


def get_metrics() -> dict:
    with _connect() as conn:
        rows = conn.execute(
            """SELECT latency_ms, cost_usd, cache_hit, fallback_used FROM requests"""
        ).fetchall()

    if not rows:
        return {"total_requests": 0}

    latencies = sorted(r[0] for r in rows if r[0] is not None)
    n = len(rows)

    def pct(p: float) -> float:
        if not latencies:
            return 0.0
        idx = min(int(p * len(latencies)), len(latencies) - 1)
        return round(latencies[idx], 1)

    return {
        "total_requests": n,
        "cache_hits": sum(r[2] for r in rows),
        "fallbacks": sum(r[3] for r in rows),
        "latency_p50_ms": pct(0.50),
        "latency_p95_ms": pct(0.95),
        "avg_cost_usd": round(sum(r[1] or 0 for r in rows) / n, 6),
        "total_cost_usd": round(sum(r[1] or 0 for r in rows), 4),
    }

init_db()