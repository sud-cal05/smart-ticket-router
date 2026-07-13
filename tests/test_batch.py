"""Batch CSV round-trip test. LLM mocked — no real API calls."""

import csv
from unittest.mock import patch

from router.schema import Priority, RoutingResult


def _ok() -> RoutingResult:
    return RoutingResult(
        category="billing", priority=Priority.high, assigned_team="Finance Ops",
        reasoning="Duplicate charge per rubric.", confidence=0.9,
    )


def test_batch_csv_round_trip(tmp_path):
    from cli import run_batch

    inp = tmp_path / "in.csv"
    out = tmp_path / "out.csv"
    inp.write_text("text\ncharged twice\ncan't log in\n", encoding="utf-8")

    usage = {"model": "gpt-4o-mini", "prompt_tokens": 100, "completion_tokens": 30}
    with patch("router.core.llm.classify", return_value=(_ok(), usage)):
        run_batch(str(inp), str(out))

    rows = list(csv.DictReader(open(out, encoding="utf-8")))
    assert len(rows) == 2
    assert rows[0]["category"] == "billing"
    assert {"category", "priority", "assigned_team", "reasoning"} <= rows[0].keys()