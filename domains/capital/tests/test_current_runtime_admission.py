"""Current interpreter admission is separate from immutable historical qualifications."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_capital_current_runtime_reports_real_default_and_required_latest():
    current = json.loads((ROOT / "config/accounting_substrate.json").read_text())
    runtime = current["runtime"]
    assert runtime["python"] == "3.15.1"
    assert runtime["databaseOwner"] == "PostgreSQL"
    assert runtime["databaseClient"] == "psycopg 3.3.6"
    assert runtime["currentSourceCutover"] == "PENDING_ACTUAL_CONSUMER_AND_DATA_PROOF"
    assert current["standing"] == "PG_NATIVE_NONLIVE_QUALIFIED_INSTALLED_CUTOVER_PENDING"
    assert "PASS_BOUNDED_SQLITE_WAL_ACCOUNTING" in current["historicalQualification"]


def test_current_capability_catalog_does_not_mislabel_old_current():
    caps = json.loads((ROOT / "config/capability_dependencies.json").read_text())["capabilities"]
    assert caps["capitalAccounting"]["pythonVersion"] == "3.15.1"
    assert caps["capitalAccounting"]["provider"] == "PostgreSQL native via psycopg"
    assert caps["capitalAccounting"]["postgresClient"] == "psycopg 3.3.6"
    assert caps["capitalAccounting"]["currentRuntimeAdmission"] == "PG_NATIVE_NONLIVE_QUALIFIED_INSTALLED_CUTOVER_PENDING"
    assert caps["research"]["pythonVersion"] == "3.15.1"
    assert caps["publicWebSocketProtocol"]["pythonVersion"] == "3.15.1"
    assert caps["research"]["parquetOwnerStanding"] == "PYARROW_26_R17_TECHNICAL_QUALIFIED_NOT_INDEPENDENT_ADMITTED"
    assert caps["research"]["independentReadbackOwnerStanding"] == "DUCKDB_1_5_5_R17_TECHNICAL_QUALIFIED"
    assert "R16" in caps["research"]["historicalParquetQualification"]


def test_actual_pg_client_version_is_installed_without_claiming_store_cutover():
    import psycopg

    assert sys.version_info[:3] == (3, 15, 1)
    assert psycopg.__version__ == "3.3.6"
    # No real server or consumer state is inspected by this version probe.
