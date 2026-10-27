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
