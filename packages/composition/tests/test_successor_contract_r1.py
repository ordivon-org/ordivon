from __future__ import annotations

import copy

import pytest

from ordivon_composition import (
    CircuitContractError,
    canonical_digest,
    compile_successor_contract,
    evaluate_successor_gates,
    validate_successor_contract,
)


def _digest(label: str) -> str:
    return canonical_digest({"fixture": label})


def valid_contract() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.successor-contract",
        "contractId": "successor:harness-rsi-r1",
        "selfBoundaryRef": {
            "id": "self:ordivon-harness",
            "digest": _digest("self-boundary"),
        },
        "predecessorRef": {
            "id": "system:harness-predecessor",
            "digest": _digest("predecessor"),
        },
        "candidateRef": {
            "id": "system:harness-candidate",
            "digest": _digest("candidate"),
        },
        "objectiveRef": {
            "id": "objective:improve-discovery",
            "digest": _digest("objective"),
        },
        "improvementProcessRef": {
            "id": "improvement-process:rsi-p5",
            "digest": _digest("process"),
        },
        "changeTargets": ["harness", "improvement-mechanism"],
        "evaluationGrounding": {
            "mode": "EXTERNALLY_ANCHORED",
            "anchors": [
                {
                    "id": "anchor:hidden-heldout",
                    "ownerId": "study:rsi",
                    "ref": "benchmark:hidden-heldout-v1",
                    "digest": _digest("hidden-heldout"),
                    "relation": "EXTERNAL_TO_CANDIDATE",
                }
            ],
        },
        "promotionPolicyRef": {
            "id": "policy:source-promotion-r1",
            "digest": _digest("promotion-policy"),
        },
        "gateRequirements": [
            {
                "id": "gate:heldout-transfer",
                "verifierOwnerId": "study:rsi",
                "supportScope": "held-out transfer under the frozen evaluation anchor only",
                "required": True,
                "anchorRefIds": ["anchor:hidden-heldout"],
            }
        ],
        "unresolvedAssumptions": [],
        "nonClaims": [
            "Mechanical closure is not promotion authority.",
            "Held-out transfer is not global intelligence improvement.",
        ],
    }


def gate_result(contract: dict, standing: str = "SATISFIED") -> dict:
    compiled = compile_successor_contract(contract)
    return {
        "schemaVersion": 1,
        "kind": "ordivon.successor-gate-result",
        "contractId": contract["contractId"],
        "contractDigest": compiled["contractDigest"],
        "gateId": "gate:heldout-transfer",
        "verifierOwnerId": "study:rsi",
        "standing": standing,
        "anchorRefIds": ["anchor:hidden-heldout"],
        "evidenceRefs": [] if standing == "UNKNOWN" else ["evidence:heldout-r1"],
        "supportScope": "held-out transfer under the frozen evaluation anchor only",
        "nonClaims": ["This verifier does not grant promotion authority."],
    }


def test_compile_is_deterministic_and_marks_recursive_mechanism_change() -> None:
    contract = valid_contract()
    first = compile_successor_contract(contract)
    second = compile_successor_contract(copy.deepcopy(contract))

    assert first == second
    assert first["recursionClass"] == "IMPROVEMENT_MECHANISM_IN_CHANGE_SET"
    assert first["evaluationGroundingMode"] == "EXTERNALLY_ANCHORED"
    assert first["externallyGrounded"] is True
    assert "grants no candidate-generation" in first["authorityBoundary"]


def test_candidate_must_differ_from_predecessor() -> None:
    contract = valid_contract()
    contract["candidateRef"] = copy.deepcopy(contract["predecessorRef"])

    with pytest.raises(CircuitContractError, match="must differ"):
        validate_successor_contract(contract)


def test_external_grounding_rejects_candidate_owned_anchor() -> None:
    contract = valid_contract()
    contract["evaluationGrounding"]["anchors"][0]["relation"] = "CANDIDATE_OWNED"

    with pytest.raises(CircuitContractError, match="cannot contain candidate-owned"):
        validate_successor_contract(contract)


def test_mixed_grounding_requires_both_anchor_relations() -> None:
    contract = valid_contract()
    contract["evaluationGrounding"]["mode"] = "MIXED"

    with pytest.raises(CircuitContractError, match="requires both"):
        validate_successor_contract(contract)


def test_unknown_gate_anchor_fails_closed() -> None:
    contract = valid_contract()
    contract["gateRequirements"][0]["anchorRefIds"] = ["anchor:missing"]

    with pytest.raises(CircuitContractError, match="unknown evaluation anchors"):
        validate_successor_contract(contract)


def test_satisfied_gate_closes_mechanics_not_promotion_or_domain_truth() -> None:
    contract = valid_contract()
    projection = evaluate_successor_gates(contract, [gate_result(contract)])

    assert projection["standing"] == "SUCCESSOR_GATES_SATISFIED"
    assert projection["mechanicalSuccessorClosure"] is True
    assert projection["promotionAuthorityEstablished"] is False
    assert projection["domainImprovementEstablished"] is False


def test_unknown_missing_or_unresolved_gate_keeps_successor_open() -> None:
    contract = valid_contract()

    missing = evaluate_successor_gates(contract, [])
    assert missing["standing"] == "SUCCESSOR_GATES_OPEN"
    assert missing["missingGateIds"] == ["gate:heldout-transfer"]

    unknown = evaluate_successor_gates(contract, [gate_result(contract, "UNKNOWN")])
    assert unknown["standing"] == "SUCCESSOR_GATES_OPEN"
    assert unknown["unknownGateIds"] == ["gate:heldout-transfer"]

    contract_with_assumption = valid_contract()
    contract_with_assumption["unresolvedAssumptions"] = ["Cross-model transfer remains unknown."]
    result = gate_result(contract_with_assumption)
    unresolved = evaluate_successor_gates(contract_with_assumption, [result])
    assert unresolved["standing"] == "SUCCESSOR_GATES_OPEN"
    assert unresolved["mechanicalSuccessorClosure"] is False


def test_unsatisfied_gate_fails_successor_closure() -> None:
    contract = valid_contract()
    projection = evaluate_successor_gates(
        contract,
        [gate_result(contract, "UNSATISFIED")],
    )
    assert projection["standing"] == "SUCCESSOR_GATES_UNSATISFIED"
    assert projection["mechanicalSuccessorClosure"] is False


def test_stale_gate_digest_and_anchor_mismatch_fail_closed() -> None:
    contract = valid_contract()
    stale = gate_result(contract)
    stale["contractDigest"] = _digest("stale")

    with pytest.raises(CircuitContractError, match="stale/different"):
        evaluate_successor_gates(contract, [stale])

    wrong_anchor = gate_result(contract)
    wrong_anchor["anchorRefIds"] = ["anchor:other"]
    with pytest.raises(CircuitContractError, match="evaluation anchor mismatch"):
        evaluate_successor_gates(contract, [wrong_anchor])


def test_self_referential_contract_is_descriptive_not_externally_grounded() -> None:
    contract = valid_contract()
    contract["evaluationGrounding"] = {
        "mode": "SELF_REFERENTIAL",
        "anchors": [
            {
                "id": "anchor:self-judge",
                "ownerId": "system:harness-candidate",
                "ref": "judge:self-v1",
                "digest": _digest("self-judge"),
                "relation": "CANDIDATE_OWNED",
            }
        ],
    }
    contract["gateRequirements"][0]["anchorRefIds"] = ["anchor:self-judge"]

    compiled = compile_successor_contract(contract)
    assert compiled["evaluationGroundingMode"] == "SELF_REFERENTIAL"
    assert compiled["externallyGrounded"] is False
