from __future__ import annotations

import copy

import pytest

from ordivon_composition import (
    CircuitContractError,
    canonical_digest,
    evaluate_interface,
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
