"""Current interpreter admission is separate from immutable historical qualifications."""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_capital_current_runtime_reports_real_default_and_required_latest():
    current = json.loads((ROOT / "config/accounting_substrate.json").read_text())
    runtime = current["runtime"]
    assert runtime["python"] == "3.15.0"
    assert runtime["sqlite"] == "3.53.1"
    assert runtime["requiredSqliteVersion"] == "3.54.0"
    assert runtime["sqliteCurrentness"] == "HOLD_OLD_EMBEDDED_SQLITE"
    assert current["standing"] == "HOLD_CURRENT_RUNTIME_LATEST_SQLITE"
    assert "PASS_BOUNDED_SQLITE_WAL_ACCOUNTING" in current["historicalQualification"]


def test_current_capability_catalog_does_not_mislabel_old_current():
    caps = json.loads((ROOT / "config/capability_dependencies.json").read_text())["capabilities"]
    assert caps["capitalAccounting"]["pythonVersion"] == "3.15.0"
    assert caps["capitalAccounting"]["sqliteVersion"] == "3.53.1"
    assert caps["capitalAccounting"]["requiredSqliteVersion"] == "3.54.0"
    assert caps["capitalAccounting"]["currentRuntimeAdmission"] == "HOLD_SQLITE_CUTOVER"
    assert caps["research"]["pythonVersion"] == "3.15.0"
    assert caps["publicWebSocketProtocol"]["pythonVersion"] == "3.15.0"
    assert caps["research"]["parquetOwnerStanding"] == "PYARROW_26_R17_TECHNICAL_QUALIFIED_NOT_INDEPENDENT_ADMITTED"
    assert caps["research"]["independentReadbackOwnerStanding"] == "DUCKDB_1_5_5_R17_TECHNICAL_QUALIFIED"
    assert "R16" in caps["research"]["historicalParquetQualification"]


def test_live_runtime_falsifier_for_embedded_sqlite():
    # In CI this is not a completion gate; it is the real observed interpreter.
    # The version-specific admission itself is in check-capabilities.
    assert sys.version_info[:3] == (3, 15, 0)
    assert sqlite3.sqlite_version in {"3.53.1", "3.54.0"}
