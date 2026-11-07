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


@pytest.mark.parametrize(
    "legacy_value",
    [
        "/tmp/legacy-worker.db",
        "postgresql://localhost/ordivon_workers",
    ],
)
def test_retired_gateway_sqlite_transport_rejected_without_opening_database(
    monkeypatch: pytest.MonkeyPatch,
    legacy_value: str,
) -> None:
    monkeypatch.setenv("ORDIVON_GATEWAY_EXTERNAL_WORKER_DB", legacy_value)
    with pytest.raises(RuntimeError, match="SQLite External Worker was retired"):
        mcp_server._external_workers_from_env()
