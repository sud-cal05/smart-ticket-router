"""Phase 0 smoke tests: prove the package imports and the harness runs. No LLM involved."""

from router.version import __version__, healthcheck


def test_package_imports():
    assert __version__ == "0.1.0"


def test_healthcheck_shape():
    result = healthcheck()
    assert result["status"] == "ok"
    assert "version" in result
