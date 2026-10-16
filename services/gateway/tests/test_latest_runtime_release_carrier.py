"""Release carrier must bind a precisely qualified Python+SQLite, never a stale managed wheel."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "packaging/install_release.sh"


def test_gateway_release_requires_qualified_embedded_sqlite_and_versioned_override():
    text = INSTALLER.read_text()
    assert "ORDIVON_GATEWAY_RELEASE_PYTHON" in text
    assert "3.15.0" in text
    assert "3.54.0" in text
    assert "sqlite3.sqlite_version" in text
    assert 'UV_PYTHON_INSTALL_DIR="$PYTHON_INSTALL_DIR"' in text
    assert '"$UV" sync --locked' in text
    assert "current.next" in text
