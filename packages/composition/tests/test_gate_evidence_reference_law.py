"""R2.1 evidence identity must be a token, not a nonempty-looking blank."""

from __future__ import annotations

import copy

import pytest
from jsonschema import Draft202012Validator

from ordivon_composition.cognitive_circuit_r1 import (
    GATE_SCHEMA,
    CircuitContractError,
    _load_json,
    validate_gate_result,
)


def result() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.composition-gate-result",
        "circuitId": "circuit:consumer",
        "manifestDigest": "sha256:" + "0" * 64,
        "gateId": "gate:outcome",
        "verifierOwnerId": "research",
        "standing": "SATISFIED",
        "evidenceRefs": ["evidence:exact-source-id"],
        "supportScope": "source identity only",
        "nonClaims": ["No domain success asserted."],
    }


@pytest.mark.parametrize(
    "ref", [" ", "\t", "\n", " evidence:valid", "evidence:valid ", "evidence:\tvalid"]
)
def test_gate_cannot_use_blank_or_whitespace_aliased_evidence_reference(ref: str) -> None:
    """A proof-reference's identity cannot be a blank or a whitespace alias."""
    datum = copy.deepcopy(result())
    datum["evidenceRefs"] = [ref]
    validator = Draft202012Validator(_load_json(GATE_SCHEMA))
    assert list(validator.iter_errors(datum)), f"accepted invalid evidence token {ref!r}"
    # The native verifier-owned gate admission must apply that same schema.
    with pytest.raises(CircuitContractError, match="schema violation"):
        validate_gate_result(
            {"circuitId": datum["circuitId"], "gateRequirements": []},
            {"manifestDigest": datum["manifestDigest"]},
            datum,
        )


def test_valid_exact_evidence_reference_remains_accepted() -> None:
    validator = Draft202012Validator(_load_json(GATE_SCHEMA))
    assert list(validator.iter_errors(result())) == []
