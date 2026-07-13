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


init_db()