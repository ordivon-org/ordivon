from __future__ import annotations

import json
import subprocess
from pathlib import Path

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


def test_r16_cross_engine_falsification_passes():
    out = subprocess.check_output(
        [str(ROOT / "scripts/run-parquet-duckdb-owner-requalification-r16")],
        cwd=ROOT,
        text=True,
    )
    result = json.loads(out)
    assert result["standing"] == "PASS_RETAIN_PYARROW_AND_DUCKDB_BOUNDED_OWNERS"
    assert result["pyarrow"]["version"] == "25.0.1"
    assert result["pyarrow"]["python3147ExecutableQualification"] == "PASS"
    assert result["duckdb"]["version"] == "1.5.5"
    assert result["externalOwnerAdmitted"] is True
    assert result["externalFinancialWriteAttempted"] is False
    assert all(result["falsification"].values())
    assert result["localBaseline"]["sameEnginePyarrowReadbackContractEquivalent"] is False
    assert result["localBaseline"]["stdlibParquetImplementationCredible"] is False
