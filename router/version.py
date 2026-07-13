"""Package version and a trivial health check used to prove the test/CI harness works end to end."""

__version__ = "0.1.0"


def healthcheck() -> dict[str, str]:
    """Return a static status payload. Replaced by real routing logic in Phase 1."""
    return {"status": "ok", "version": __version__}
