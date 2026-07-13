"""Input guards: run BEFORE any API call. Reject empty input (save a token),
truncate absurdly long input head+tail, and redact PII so it never leaves the machine."""

import re

MAX_CHARS = 8000
_HEAD = 5000
_TAIL = 2000

_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE_RE = re.compile(r"\b(?:\+?\d[\d\s().-]{7,}\d)\b")


class EmptyInputError(ValueError):
    """Raised when the ticket text is empty or whitespace only."""


def validate(text: str) -> str:
    """Raise EmptyInputError if blank; otherwise return the stripped text."""
    if text is None or not text.strip():
        raise EmptyInputError("Ticket text is empty.")
    return text.strip()


def truncate(text: str) -> str:
    """Keep head+tail with a marker if the text exceeds MAX_CHARS."""
    if len(text) <= MAX_CHARS:
        return text
    return (
        text[:_HEAD]
        + "\n\n[...TRUNCATED FOR LENGTH — middle omitted...]\n\n"
        + text[-_TAIL:]
    )


def redact_pii(text: str) -> str:
    """Mask emails and phone numbers before the text reaches the API."""
    text = _EMAIL_RE.sub("[EMAIL]", text)
    text = _PHONE_RE.sub("[PHONE]", text)
    return text


def prepare(text: str) -> str:
    """Full input pipeline: validate -> truncate -> redact."""
    return redact_pii(truncate(validate(text)))