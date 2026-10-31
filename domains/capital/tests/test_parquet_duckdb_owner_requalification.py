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


def test_r17_qualification_uses_current_declared_capital_python_version():
    import ast

    current = (ROOT / ".python-version").read_text().strip()
    assert current == "3.15.1"
    source = (ROOT / "tools/qualification/parquet_duckdb_owner_r17.py").read_text()
    parsed = ast.parse(source)
    expected = tuple(map(int, current.split(".")))
    guarded_versions = []
    for node in ast.walk(parsed):
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Subscript):
            if (isinstance(node.left.value, ast.Attribute)
                    and node.left.value.attr == "version_info"
                    and isinstance(node.left.value.value, ast.Name)
                    and node.left.value.value.id == "sys"):
                for comparator in node.comparators:
                    if isinstance(comparator, ast.Tuple):
                        values = tuple(v.value for v in comparator.elts
                                       if isinstance(v, ast.Constant))
                        guarded_versions.append(values)
    assert expected in guarded_versions


@pytest.mark.provider_qualification
def test_r17_cross_engine_falsification_latest_pyarrow_python3151():
    out = subprocess.check_output(
        [str(ROOT / "scripts/run-parquet-duckdb-owner-requalification-r17")],
        cwd=ROOT, text=True,
    )
    result = json.loads(out)
    assert result["kind"] == "ordivon.capital.research.parquet-owner-requalification-r17"
    assert result["pyarrow"]["version"] == "26.0.0"
    assert result["pyarrow"]["python3151ExecutableQualification"] == "PASS"
    assert result["duckdb"]["version"] == "1.5.5"
    assert result["externalFinancialWriteAttempted"] is False
    assert result["externalOwnerAdmitted"] is False
    assert result["standing"] == "PASS_R17_CROSS_ENGINE_TECHNICAL_QUALIFICATION"
    assert all(result["falsification"].values())
