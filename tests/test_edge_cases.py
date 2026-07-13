"""Edge-case behavior tests. Guard/injection/PII cases run without the API;
they assert the system's structural handling, not the LLM's judgment."""

import pytest

from router.guards import EmptyInputError, prepare


def test_empty_string_raises():
    with pytest.raises(EmptyInputError):
        prepare("")


def test_whitespace_only_raises():
    with pytest.raises(EmptyInputError):
        prepare("    \n\t  ")


def test_long_input_is_truncated_before_send():
    huge = "spam " * 5000
    out = prepare(huge)
    assert len(out) < len(huge)
    assert "TRUNCATED" in out


def test_pii_never_leaves_in_prepared_text():
    out = prepare("contact me at alice@corp.com or 555-123-4567 about my bug")
    assert "alice@corp.com" not in out
    assert "[EMAIL]" in out