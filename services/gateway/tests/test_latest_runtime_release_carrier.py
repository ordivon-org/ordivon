"""Gateway release selection must not require an unused SQLite engine.

The legacy external pull-worker path owns the only Gateway SQLite runtime gate,
not the main Gateway release installer or the Skills/Host/Runtime MCP transport.
"""

from pathlib import Path

import pytest

from ordivon_gateway import external_worker, mcp_server

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "packaging/install_release.sh"


def test_gateway_release_checks_python_not_legacy_sqlite() -> None:
    text = INSTALLER.read_text(encoding="utf-8")
    assert "ORDIVON_GATEWAY_RELEASE_PYTHON" in text
    assert "3.15.1" in text
    assert "sqlite3.sqlite_version" not in text
    assert "import sqlite3" not in text
    assert 'UV_PYTHON_INSTALL_DIR="$PYTHON_INSTALL_DIR"' in text
    assert '"$UV" sync --locked' in text
    assert "current.next" in text


def test_default_gateway_needs_no_database(monkeypatch):
    monkeypatch.delenv("ORDIVON_GATEWAY_EXTERNAL_WORKER_DB", raising=False)

    def forbidden(*args, **kwargs):
        raise AssertionError("disabled feature opened a database")

    monkeypatch.setattr(external_worker.psycopg, "connect", forbidden)
    assert mcp_server._external_workers_from_env() is None


@pytest.mark.parametrize("value", ["/tmp/legacy-worker.db", "", "postgresql://", "dbname=workers"])
def test_worker_requires_explicit_pg_dsn(value):
    with pytest.raises(ValueError, match="explicit PostgreSQL DSN"):
        external_worker.ExternalPullWorkerTransport(value)


def test_explicit_worker_dsn_uses_pg_backend(monkeypatch, pg_dsn):
    monkeypatch.setenv("ORDIVON_GATEWAY_EXTERNAL_WORKER_DB", pg_dsn)
    transport = mcp_server._external_workers_from_env()
    assert transport is not None
    assert transport.dsn == pg_dsn


def test_legacy_path_fails_closed(monkeypatch):
    monkeypatch.setenv("ORDIVON_GATEWAY_EXTERNAL_WORKER_DB", "/tmp/legacy-worker.db")
    with pytest.raises(ValueError, match="explicit PostgreSQL DSN"):
        mcp_server._external_workers_from_env()
