"""Current Capital PG client check is separate from the installed store cutover."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_capabilities_enforce_python_and_postgresql_client_versions():
    source = (ROOT / "scripts/check-capabilities").read_text()
    assert '"pyarrow": "26.0.0"' in source
    assert 'sys.version.split()[0] != "3.15.1"' in source
    assert '"psycopg": "3.3.6"' in source
    assert "sqlite3.sqlite_version" not in source
    assert 'ORDIVON_CAPITAL_PYTHON' in source


def test_current_pg_client_replaces_obsolete_sqlite_runtime_gate():
    source = (ROOT / "scripts/check-capabilities").read_text()
    assert '"psycopg": "3.3.6"' in source
    assert 'sqlite3.sqlite_version' not in source
    assert '"databaseOwner": "PostgreSQL"' in source
    assert '"installedCutover": "PENDING"' in source
