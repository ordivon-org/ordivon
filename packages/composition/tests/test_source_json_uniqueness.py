"""The same source cannot encode two conflicting meanings for one LEGO key."""

from __future__ import annotations

from pathlib import Path

import pytest

from ordivon_composition.cognitive_circuit_r1 import (
    CircuitContractError,
)
from ordivon_composition.cognitive_circuit_r1 import (
    _load_json as circuit_load,
)
from ordivon_composition.interface_contract_r2 import _load_json as interface_load
from ordivon_composition.successor_contract_r1 import _load_json as successor_load
from ordivon_composition.verification_obligation_r1 import _load_json as verifier_load


@pytest.mark.parametrize(
    "load",
    [circuit_load, interface_load, verifier_load, successor_load],
)
def test_source_bound_lego_contract_rejects_ambiguous_nested_json_object(
    tmp_path: Path,
    load,
) -> None:
    """Duplicate keys are not a single typed function; last-write-wins is ambiguous."""
    source = tmp_path / "contract.json"
    source.write_text(
        '{"owner":"Harness","gate":{"standing":"UNKNOWN","standing":"SATISFIED"}}',
        encoding="utf-8",
    )
    with pytest.raises(CircuitContractError, match="duplicate JSON key.*standing"):
        load(source)


@pytest.mark.parametrize(
    "load",
    [circuit_load, interface_load, verifier_load, successor_load],
)
def test_source_bound_lego_contract_rejects_non_json_numeric_constants(
    tmp_path: Path,
    load,
) -> None:
    """NaN is not an RFC-8259 JSON value and cannot be a proof-bearing SourceCut."""
    source = tmp_path / "contract.json"
    source.write_text('{"owner":"Runtime","evidence":NaN}', encoding="utf-8")
    with pytest.raises(CircuitContractError, match="invalid JSON constant.*NaN"):
        load(source)
