from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_exact_contract_requires_distinct_parquet_producer_and_readback_engine():
    contract = json.loads(
        (ROOT / "contracts/parquet-materialization-readback-v1.json").read_text()
    )
    assert contract["standing"] == "ACTIVE_EXACT_CONTRACT"
    assert contract["materialization"]["producer"] == "PyArrow"
    assert contract["independentReadback"]["consumer"] == "DuckDB"
    assert "must not be the same" in contract["independentReadback"]["independenceRule"]
    assert contract["externalFinancialWritesAllowed"] is False


def test_r16_historical_source_kept_immutable():
    """Do not rewrite 25.0.1 R16 evidence while moving live acceptance to R17."""
    import hashlib
    archived = ROOT / "tools/qualification/parquet_duckdb_owner_r16.py"
    assert hashlib.sha256(archived.read_bytes()).hexdigest() == (
        "44fee1427550108cb74e90d71276dcdaa8d82343fbc2e215e86c405716068911"
    )
    assert '25.0.1' in archived.read_text()


@pytest.mark.provider_qualification
def test_r17_cross_engine_falsification_latest_pyarrow_python3150():
    out = subprocess.check_output(
        [str(ROOT / "scripts/run-parquet-duckdb-owner-requalification-r17")],
        cwd=ROOT, text=True,
    )
    result = json.loads(out)
    assert result["kind"] == "ordivon.capital.research.parquet-owner-requalification-r17"
    assert result["pyarrow"]["version"] == "26.0.0"
    assert result["pyarrow"]["python3150ExecutableQualification"] == "PASS"
    assert result["duckdb"]["version"] == "1.5.5"
    assert result["externalFinancialWriteAttempted"] is False
    assert result["externalOwnerAdmitted"] is False
    assert result["standing"] == "PASS_R17_CROSS_ENGINE_TECHNICAL_QUALIFICATION"
    assert all(result["falsification"].values())
