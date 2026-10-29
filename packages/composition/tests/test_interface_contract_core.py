from __future__ import annotations

import copy

import pytest

from ordivon_composition import (
    CircuitContractError,
    canonical_digest,
    evaluate_interface,
    inspect_lego_declaration,
)


def _digest(label: str) -> str:
    return canonical_digest({"fixture": label})


def _circuit_ref(label: str = "circuit") -> dict:
    return {"id": "circuit:test-interface", "digest": _digest(label)}


def _observation(*, digest: str | None = None, circuit_ref: dict | None = None) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.interface-contract-observation",
        "observationId": "observation:test",
        "circuitRef": copy.deepcopy(circuit_ref or _circuit_ref()),
        "producerOwnerId": "owner:test",
        "sourceKind": "direct-owner-observation",
        "sourceRef": "evidence:test",
        "sourceDigest": _digest("source"),
        "interfaceRef": {
            "id": "interface:test",
            "digest": digest or _digest("required"),
        },
        "projectedAuthorityVersionRef": None,
        "liveAuthorityVersionRef": None,
        "nonClaims": ["Point-in-time observation only."],
    }


def _expectation(*, circuit_ref: dict | None = None) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.interface-contract-expectation",
        "expectationId": "expectation:test",
        "consumerId": "consumer:test",
        "circuitRef": copy.deepcopy(circuit_ref or _circuit_ref()),
        "interfaceId": "interface:test",
        "requiredDigest": _digest("required"),
        "acceptedSourceKinds": ["direct-owner-observation", "retained-projection"],
        "acceptedAlternates": [],
        "supportScope": "test seam only",
        "nonClaims": ["Compatibility is not domain acceptance."],
    }


def test_exact_match_is_point_in_time_and_admissible() -> None:
    result = evaluate_interface(_observation(), _expectation())
    assert result["compatibilityStanding"] == "EXACT_MATCH"
    assert result["currentnessStanding"] == "POINT_IN_TIME_OBSERVED"
    assert result["evidenceAdmissibility"] == "ADMISSIBLE"
    assert result["domainAcceptanceEstablished"] is False


def test_alternate_requires_explicit_compatibility_evidence() -> None:
    alternate = _digest("alternate")
    observation = _observation(digest=alternate)
    exp = _expectation()

    assert evaluate_interface(observation, exp)["compatibilityStanding"] == "MISMATCH"

    exp["acceptedAlternates"] = [
        {
            "digest": alternate,
            "compatibilityEvidenceRef": "evidence:explicit-compatibility",
        }
    ]
    result = evaluate_interface(observation, exp)
    assert result["compatibilityStanding"] == "COMPATIBLE_BY_DECLARATION"
    assert result["evidenceAdmissibility"] == "ADMISSIBLE"


def test_circuit_binding_mismatch_fails_closed() -> None:
    observation = _observation(circuit_ref=_circuit_ref("a"))
    exp = _expectation(circuit_ref=_circuit_ref("b"))
    with pytest.raises(CircuitContractError, match="circuitRef mismatch"):
        evaluate_interface(observation, exp)


def test_unmodeled_git_recency_cannot_mint_currentness() -> None:
    observation = _observation()
    observation["gitHead"] = "deadbeef"
    with pytest.raises(CircuitContractError, match="schema violation"):
        evaluate_interface(observation, _expectation())


def _strict_r21_lego() -> dict:
    # Candidate specification is not a checked theorem or implementation.
    return {
        "id": "lego:core:even-adapter",
        "responsibility": "Map a bounded integer to an even integer",
        "goal": "Admit only well-defined pure semantic connectors",
        "consumerRef": "lego:core:even-consumer",
        "semanticProfile": "finite-bitvector-pure-sequential",
        "behavioralContract": {
            "assumption": {"predicate": "x is a UInt4"},
            "guarantee": {"predicate": "y is a UInt4 and y is even"},
            "totality": {"predicate": "each accepted x produces one y"},
        },
        "representation": {
            "relation": "source model to UInt4 identity",
            "concreteWitness": "x=1 is admitted by the source model",
        },
        "observationBoundary": {
            "scope": "pure deterministic UInt4 result only",
            "outputs": ["y"],
            "effects": [],
        },
        "I": {"type": "UInt4", "meaning": "unsigned four-bit input"},
        "O": {"type": "UInt4", "meaning": "even four-bit output"},
        "S": {"type": "Unit", "meaning": "stateless by model specification"},
        "pre": {"predicate": "0 <= x < 16"},
        "post": {"predicate": "y = (2*x) mod 16"},
        "inv": {"predicate": "external effects are absent"},
        "eff": {"kind": "none", "assumption": "pure model; code not verified"},
        "c": {
            "standing": "UNKNOWN",
            "metric": "elapsed milliseconds",
            "reason": "no runtime measurement has been made",
        },
        "epsilon": {"standing": "EXACT_DECLARED", "value": "0"},
        "prov": {"sourceCut": "source:immutable", "specRef": "spec:even-adapter"},
        "unfold": [],
        "acceptance": {
            "criterion": "checker-backed valid connection, wrong type rejected",
            "observer": "consumer:even-consumer",
            "method": "finite UInt4 checker with explicit failure observation",
            "target": "all 16 legal valuations satisfy the declared postcondition",
            "baseline": {"standing": "SPECIFICATION", "ref": "spec:even-adapter"},
            "evidence": {
                "standing": "NOT_OBSERVED",
                "reason": "checker receipt not provided",
            },
        },
    }


def test_full_r21_tuple_is_only_a_declaration_not_a_formal_proof() -> None:
    result = inspect_lego_declaration(_strict_r21_lego())
    assert result["declarationStanding"] == "DECLARATION_COMPLETE_UNPROVED"
    assert result["missingCoordinates"] == []
    assert result["invalidCoordinates"] == []
    assert result["modelProofStanding"] == "UNKNOWN"
    assert result["implementationRefinement"] == "UNKNOWN"
    assert result["installedCurrentness"] == "UNKNOWN"
    assert result["promotionAdmissible"] is False
    assert result["declarationDigest"].startswith("sha256:")


@pytest.mark.parametrize(
    "missing",
    [
        "S",
        "pre",
        "post",
        "inv",
        "eff",
        "c",
        "epsilon",
        "prov",
        "unfold",
        "consumerRef",
        "semanticProfile",
    ],
)
def test_missing_mandatory_r21_coordinate_is_unqualified(missing: str) -> None:
    lego = _strict_r21_lego()
    del lego[missing]
    result = inspect_lego_declaration(lego)
    assert result["declarationStanding"] == "CANDIDATE_UNQUALIFIED"
    assert missing in result["missingCoordinates"]
    assert result["promotionAdmissible"] is False


@pytest.mark.parametrize(
    "key,value",
    [
        ("I", "UInt4"),
        ("S", None),
        ("pre", {}),
        ("post", {"predicate": ""}),
        ("eff", None),
        ("c", {"metric": "time"}),
        ("epsilon", True),
        ("prov", {}),
        ("unfold", "atomic"),
    ],
)
def test_malformed_r21_coordinate_cannot_claim_qualification(key: str, value: object) -> None:
    lego = _strict_r21_lego()
    lego[key] = value
    result = inspect_lego_declaration(lego)
    assert result["declarationStanding"] == "CANDIDATE_UNQUALIFIED"
    assert key in result["invalidCoordinates"]
    assert result["modelProofStanding"] == "UNKNOWN"


def test_strict_r21_public_cli_is_inspection_not_formal_qualification(tmp_path) -> None:
    import json
    import subprocess
    import sys

    path = tmp_path / "lego.json"
    lego = _strict_r21_lego()
    # A caller-authored proof claim must not be accepted as a checker receipt.
    lego["modelProofStanding"] = "PROVED"
    path.write_text(json.dumps(lego), encoding="utf-8")
    run = subprocess.run(
        [
            sys.executable,
            "-c",
            "from ordivon_composition.interface_contract_r2 import main; raise SystemExit(main())",
            "inspect-lego",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, run.stderr
    result = json.loads(run.stdout)
    assert result["declarationStanding"] == "DECLARATION_COMPLETE_UNPROVED"
    assert result["modelProofStanding"] == "UNKNOWN"
    assert result["promotionAdmissible"] is False


@pytest.mark.parametrize(
    "coordinate", ["behavioralContract", "representation", "observationBoundary"]
)
def test_missing_behavior_semantics_is_not_r21_declared(coordinate: str) -> None:
    lego = _strict_r21_lego()
    del lego[coordinate]
    result = inspect_lego_declaration(lego)
    assert result["declarationStanding"] == "CANDIDATE_UNQUALIFIED"
    assert coordinate in result["missingCoordinates"]
    assert result["modelProofStanding"] == "UNKNOWN"


def test_placeholder_assume_guarantee_is_not_a_complete_declaration() -> None:
    lego = _strict_r21_lego()
    lego["behavioralContract"]["guarantee"] = {"predicate": ""}
    result = inspect_lego_declaration(lego)
    assert result["declarationStanding"] == "CANDIDATE_UNQUALIFIED"
    assert "behavioralContract" in result["invalidCoordinates"]


# Consumer-driven R2.1 admission: having a free-form acceptance criterion is
# insufficient to tell an Agent how/whether the declared goal will be checked.
@pytest.mark.parametrize(
    "acceptance",
    [
        {"criterion": "must return an acceptable result"},
        {
            "criterion": "must return an acceptable result",
            "observer": "client",
            "method": "run a finite test",
            "target": "true",
            "baseline": {"standing": "UNKNOWN"},
            "evidence": {"standing": "NOT_OBSERVED"},
        },
        {
            "criterion": "must return an acceptable result",
            "observer": "client",
            "method": "run a finite test",
            "target": "true",
            "baseline": {"standing": "SPECIFICATION"},
            "evidence": {"standing": "NOT_OBSERVED", "reason": "not executed"},
        },
    ],
)
def test_declared_acceptance_requires_measurement_and_honest_baseline(
    acceptance: dict,
) -> None:
    lego = _strict_r21_lego()
    lego["acceptance"] = acceptance
    result = inspect_lego_declaration(lego)
    assert result["declarationStanding"] == "CANDIDATE_UNQUALIFIED"
    assert "acceptance" in result["invalidCoordinates"]
    assert result["promotionAdmissible"] is False


def test_unknown_cost_requires_explicit_reason_for_agent_decision() -> None:
    lego = _strict_r21_lego()
    lego["c"] = {"standing": "UNKNOWN", "metric": "elapsed milliseconds"}
    result = inspect_lego_declaration(lego)
    assert result["declarationStanding"] == "CANDIDATE_UNQUALIFIED"
    assert "c" in result["invalidCoordinates"]
    assert result["modelProofStanding"] == "UNKNOWN"


def test_unknown_external_evidence_is_not_claimed_as_accepted() -> None:
    lego = _strict_r21_lego()
    lego["acceptance"] = {
        "criterion": "finite property checked on all UInt4 inputs",
        "observer": "consumer:finite-checker",
        "method": "checked finite enumeration",
        "target": "all 16 legal input valuations satisfy guarantee",
        "baseline": {"standing": "SPECIFICATION", "ref": "contract:even-adapter-v1"},
        "evidence": {"standing": "NOT_OBSERVED", "reason": "checker not yet run"},
    }
    lego["c"]["reason"] = "no measured runtime bound"
    result = inspect_lego_declaration(lego)
    assert result["declarationStanding"] == "DECLARATION_COMPLETE_UNPROVED"
    assert result["modelProofStanding"] == "UNKNOWN"
    assert result["promotionAdmissible"] is False
