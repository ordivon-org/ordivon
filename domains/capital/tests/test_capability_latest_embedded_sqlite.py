"""Current capability admission must not certify stale interpreter/SQLite evidence."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_capabilities_enforce_latest_runtime_and_sqlite():
    source = (ROOT / "scripts/check-capabilities").read_text()
    assert '"pyarrow": "26.0.0"' in source
    assert 'sys.version.split()[0] != "3.15.1"' in source
    assert 'sqlite3.sqlite_version != "3.54.0"' in source
    assert 'ORDIVON_CAPITAL_PYTHON' in source
