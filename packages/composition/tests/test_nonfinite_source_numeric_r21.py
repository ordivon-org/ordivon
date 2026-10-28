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
