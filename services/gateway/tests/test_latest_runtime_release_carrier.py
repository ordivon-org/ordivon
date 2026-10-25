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


def test_default_gateway_does_not_require_any_sqlite_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ORDIVON_GATEWAY_EXTERNAL_WORKER_DB", raising=False)
    monkeypatch.setattr(external_worker.sqlite3, "sqlite_version", "0.0.0")
    assert mcp_server._external_workers_from_env() is None


def test_explicit_legacy_worker_fails_closed_on_unqualified_sqlite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ORDIVON_GATEWAY_EXTERNAL_WORKER_DB", "/tmp/legacy-worker.db")
    monkeypatch.setattr(external_worker.sqlite3, "sqlite_version", "3.53.1")
    with pytest.raises(RuntimeError, match="legacy external worker requires SQLite 3.54.0"):
        mcp_server._external_workers_from_env()


def test_legacy_worker_cannot_misinterpret_postgres_dsn_as_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "ORDIVON_GATEWAY_EXTERNAL_WORKER_DB",
        "postgresql://localhost/ordivon_workers",
    )
    monkeypatch.setattr(external_worker.sqlite3, "sqlite_version", "3.54.0")
    with pytest.raises(RuntimeError, match="not a PostgreSQL backend"):
        mcp_server._external_workers_from_env()


def test_explicit_qualified_legacy_worker_uses_existing_backend(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "legacy-worker.db"
    monkeypatch.setenv("ORDIVON_GATEWAY_EXTERNAL_WORKER_DB", str(path))
    monkeypatch.setattr(external_worker.sqlite3, "sqlite_version", "3.54.0")
    constructed: list[str] = []
    sentinel = object()

    def fake_transport(value: str) -> object:
        constructed.append(value)
        return sentinel

    monkeypatch.setattr(mcp_server, "ExternalPullWorkerTransport", fake_transport)
    assert mcp_server._external_workers_from_env() is sentinel
    assert constructed == [str(path)]
