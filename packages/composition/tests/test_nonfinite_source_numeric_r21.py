"""R2.1 representation admission: a JSON number must stay finite after decoding.

The existing four object consumers share one source parser; task-local proof
arrays use the same numeric admission predicate. This protects the source
representation boundary, not actual installed effects or mathematical proof.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from ordivon_composition.cognitive_circuit_r1 import CircuitContractError
from ordivon_composition.cognitive_circuit_r1 import _load_json as circuit_load
from ordivon_composition.interface_contract_r2 import _load_json as interface_load
from ordivon_composition.successor_contract_r1 import _load_json as successor_load
from ordivon_composition.verification_obligation_r1 import (
    _load_json as obligation_load,
)
from ordivon_composition.verification_obligation_r1 import (
    _load_task_local_json_list,
)


@pytest.mark.parametrize("load", (circuit_load, interface_load, successor_load, obligation_load))
@pytest.mark.parametrize("overflow", ("1e309", "-1e309"))
def test_nested_object_source_rejects_nonfinite_json_number(
    tmp_path: Path, load, overflow: str
) -> None:
    source = tmp_path / "contract.json"
    source.write_text('{"contract":{"evidence":{"weight":' + overflow + "}}}", encoding="utf-8")
    with pytest.raises(CircuitContractError, match="non-finite JSON number"):
        load(source)


@pytest.mark.parametrize("overflow", ("1e309", "-1e309"))
def test_task_local_proof_array_rejects_nonfinite_json_number(
    tmp_path: Path, overflow: str
) -> None:
    source = tmp_path / "obligations.json"
    source.write_text('[{"claim":{"weight":' + overflow + "}}]", encoding="utf-8")
    with pytest.raises(CircuitContractError, match="non-finite JSON number"):
        _load_task_local_json_list(source)


def test_finite_numeric_input_remains_accepted(tmp_path: Path) -> None:
    source = tmp_path / "contract.json"
    source.write_text('{"value":1e308,"zero":-0.0}', encoding="utf-8")
    actual = circuit_load(source)
    assert math.isfinite(actual["value"]) and actual["value"] > 0
    assert actual["zero"] == 0

    source.write_text('[{"value":1e308,"zero":-0.0}]', encoding="utf-8")
    array = _load_task_local_json_list(source)
    assert math.isfinite(array[0]["value"])


# These lexical pairs are mathematically DISTINCT decimal values, but the
# platform float parser merges each pair into one identical digest. Refuse
# only the lossy input; equivalent decimal spellings remain legal.
@pytest.mark.parametrize(
    "lossy,canonical",
    [
        ("1e-324", "0.0"),
        ("-1e-400", "-0.0"),
        ("0.10000000000000001", "0.1"),
        ("9007199254740993.0", "9007199254740992.0"),
        ("1.0000000000000001", "1.0"),
    ],
)
@pytest.mark.parametrize("load", (circuit_load, interface_load, successor_load, obligation_load))
def test_shared_object_evidence_parser_refuses_float_precision_alias(
    tmp_path: Path, load, lossy: str, canonical: str
) -> None:
    source = tmp_path / "evidence.json"
    source.write_text('{"gate":{"weight":' + lossy + "}}", encoding="utf-8")
    with pytest.raises(CircuitContractError, match="lossy JSON numeric evidence"):
        load(source)
    source.write_text('{"gate":{"weight":' + canonical + "}}", encoding="utf-8")
    assert isinstance(load(source)["gate"]["weight"], float)


@pytest.mark.parametrize(
    "lossy,canonical",
    [
        ("1e-324", "0.0"),
        ("0.10000000000000001", "0.1"),
        ("9007199254740993.0", "9007199254740992.0"),
    ],
)
def test_shared_obligation_array_parser_refuses_float_precision_alias(
    tmp_path: Path, lossy: str, canonical: str
) -> None:
    from ordivon_composition.cognitive_circuit_r1 import canonical_digest

    source = tmp_path / "obligations.json"
    source.write_text('[{"weight":' + lossy + "}]", encoding="utf-8")
    with pytest.raises(CircuitContractError, match="lossy JSON numeric evidence"):
        _load_task_local_json_list(source)
    source.write_text('[{"weight":' + canonical + "}]", encoding="utf-8")
    decoded = _load_task_local_json_list(source)
    assert canonical_digest(decoded) == canonical_digest([{"weight": float(canonical)}])


@pytest.mark.parametrize("equivalent", ("1.0", "1e0", "1.000", "0.10", "1e308", "-0.0"))
def test_numeric_equivalent_lexemes_keep_original_float_consumer(
    tmp_path: Path, equivalent: str
) -> None:
    source = tmp_path / "numeric.json"
    source.write_text('{"weight":' + equivalent + "}", encoding="utf-8")
    parsed = circuit_load(source)
    assert isinstance(parsed["weight"], float)
    assert math.isfinite(parsed["weight"])


@pytest.mark.parametrize(
    "module,args",
    [
        ("ordivon_composition.verification_obligation_r1", ["compile-obligations"]),
        ("ordivon_composition.cognitive_circuit_r1", ["compile"]),
    ],
)
@pytest.mark.parametrize("lossy", ("1e-324", "0.10000000000000001", "9007199254740993.0"))
def test_native_consumers_refuse_lossy_evidence_before_hash_or_proof(
    tmp_path: Path, module: str, args: list[str], lossy: str
) -> None:
    import subprocess
    import sys

    source = tmp_path / "incoming.json"
    source.write_text('{"evidence":{"weight":' + lossy + "}}", encoding="utf8")
    result = subprocess.run(
        [sys.executable, "-m", module, *args, str(source)],
        capture_output=True,
        text=True,
        check=False,
        timeout=18,
    )
    assert result.returncode != 0
    assert "lossy JSON numeric evidence" in result.stderr
    assert "Traceback" not in result.stderr
    assert result.stdout == ""
