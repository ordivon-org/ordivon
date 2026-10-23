#!/usr/bin/env python3
"""Task-local Successor Contract R1 mechanics.

This module binds one exact predecessor to one exact candidate successor and
evaluates verifier-owned succession gates. It deliberately does not generate
candidates, choose objectives, define domain metrics, grant promotion authority,
write Git/release state, or declare that a candidate is globally better.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .cognitive_circuit_r1 import (
    CircuitContractError,
    _load_json,
    _validate_schema,
    canonical_digest,
)

ROOT = Path(__file__).resolve().parent
CONTRACT_SCHEMA = ROOT / "schemas" / "successor-contract-v1.schema.json"
GATE_SCHEMA = ROOT / "schemas" / "successor-gate-result-v1.schema.json"


def _unique_by_id(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = row["id"]
        if row_id in result:
            raise CircuitContractError(f"duplicate {label} id: {row_id}")
        result[row_id] = row
    return result


def _derived_recursion_class(change_targets: list[str]) -> str:
    targets = set(change_targets)
    if "improvement-mechanism" in targets:
        return "IMPROVEMENT_MECHANISM_IN_CHANGE_SET"
    if "evaluator" in targets:
        return "EVALUATOR_IN_CHANGE_SET"
    return "PERSISTENT_SELF_CHANGE_NO_MECHANISM_RECURSION"


def validate_successor_contract(value: dict[str, Any]) -> None:
    _validate_schema(value, CONTRACT_SCHEMA, "successor contract")

    if value["predecessorRef"] == value["candidateRef"]:
        raise CircuitContractError("predecessorRef and candidateRef must differ")

    anchors = _unique_by_id(value["evaluationGrounding"]["anchors"], "evaluation anchor")
    gates = _unique_by_id(value["gateRequirements"], "successor gate requirement")

    anchor_ids = set(anchors)
    external_anchor_ids = {
        anchor_id
        for anchor_id, anchor in anchors.items()
        if anchor["relation"] == "EXTERNAL_TO_CANDIDATE"
    }
    candidate_owned_anchor_ids = anchor_ids - external_anchor_ids

    for gate_id, gate in gates.items():
        missing = sorted(set(gate["anchorRefIds"]) - anchor_ids)
        if missing:
            raise CircuitContractError(
                f"gate {gate_id} references unknown evaluation anchors: {missing}"
            )

    mode = value["evaluationGrounding"]["mode"]
    referenced_by_required = set()
    for gate in gates.values():
        if gate["required"]:
            referenced_by_required.update(gate["anchorRefIds"])

    if mode == "EXTERNALLY_ANCHORED":
        if candidate_owned_anchor_ids:
            raise CircuitContractError(
                "EXTERNALLY_ANCHORED evaluation cannot contain candidate-owned anchors"
            )
        if not referenced_by_required.intersection(external_anchor_ids):
            raise CircuitContractError(
                "EXTERNALLY_ANCHORED evaluation requires a required gate bound to an external anchor"
            )
    elif mode == "MIXED":
        if not external_anchor_ids or not candidate_owned_anchor_ids:
            raise CircuitContractError(
                "MIXED evaluation requires both external and candidate-owned anchors"
            )
        if not referenced_by_required.intersection(external_anchor_ids):
            raise CircuitContractError(
                "MIXED evaluation requires a required gate bound to an external anchor"
            )
    else:
        if external_anchor_ids:
            raise CircuitContractError(
                "SELF_REFERENTIAL evaluation cannot contain external anchors"
            )


def compile_successor_contract(value: dict[str, Any]) -> dict[str, Any]:
    validate_successor_contract(value)
    contract_digest = canonical_digest(value)
    anchors = value["evaluationGrounding"]["anchors"]
    required_gate_ids = sorted(gate["id"] for gate in value["gateRequirements"] if gate["required"])
    projection: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.successor-contract-compiled",
        "truthRole": "task-local-non-authoritative-succession-projection",
        "contractId": value["contractId"],
        "contractDigest": contract_digest,
        "selfBoundaryRef": value["selfBoundaryRef"],
        "predecessorRef": value["predecessorRef"],
        "candidateRef": value["candidateRef"],
        "objectiveRef": value["objectiveRef"],
        "improvementProcessRef": value["improvementProcessRef"],
        "changeTargets": sorted(value["changeTargets"]),
        "recursionClass": _derived_recursion_class(value["changeTargets"]),
        "evaluationGroundingMode": value["evaluationGrounding"]["mode"],
        "externallyGrounded": any(
            anchor["relation"] == "EXTERNAL_TO_CANDIDATE" for anchor in anchors
        ),
        "evaluationAnchorIds": sorted(anchor["id"] for anchor in anchors),
        "promotionPolicyRef": value["promotionPolicyRef"],
        "requiredGateIds": required_gate_ids,
        "unresolvedAssumptions": sorted(value["unresolvedAssumptions"]),
        "authorityBoundary": (
            "This projection grants no candidate-generation, evaluation, mutation, "
            "promotion, deployment, Git, release, or domain-verdict authority."
        ),
    }
    projection["compiledDigest"] = canonical_digest(projection)
    return projection


def validate_successor_gate_result(
    contract: dict[str, Any],
    compiled: dict[str, Any],
    result: dict[str, Any],
) -> None:
    _validate_schema(result, GATE_SCHEMA, "successor gate result")

    if result["contractId"] != contract["contractId"]:
        raise CircuitContractError(f"gate {result['gateId']} binds a different contractId")
    if result["contractDigest"] != compiled["contractDigest"]:
        raise CircuitContractError(
            f"gate {result['gateId']} binds a stale/different successor contract digest"
        )

    gates = {gate["id"]: gate for gate in contract["gateRequirements"]}
    gate = gates.get(result["gateId"])
    if gate is None:
        raise CircuitContractError(f"unknown successor gate result: {result['gateId']}")
    if result["verifierOwnerId"] != gate["verifierOwnerId"]:
        raise CircuitContractError(f"gate {result['gateId']} verifier owner mismatch")
    if result["supportScope"] != gate["supportScope"]:
        raise CircuitContractError(f"gate {result['gateId']} support scope mismatch")
    if set(result["anchorRefIds"]) != set(gate["anchorRefIds"]):
        raise CircuitContractError(f"gate {result['gateId']} evaluation anchor mismatch")


def evaluate_successor_gates(
    contract: dict[str, Any],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    compiled = compile_successor_contract(contract)
    by_gate: dict[str, dict[str, Any]] = {}
    for result in results:
        validate_successor_gate_result(contract, compiled, result)
        gate_id = result["gateId"]
        if gate_id in by_gate:
            raise CircuitContractError(f"duplicate successor gate result: {gate_id}")
        by_gate[gate_id] = result

    required = {gate["id"]: gate for gate in contract["gateRequirements"] if gate["required"]}
    missing = sorted(set(required) - set(by_gate))
    unsatisfied = sorted(
        gate_id
        for gate_id in required
        if gate_id in by_gate and by_gate[gate_id]["standing"] == "UNSATISFIED"
    )
    unknown = sorted(
        gate_id
        for gate_id in required
        if gate_id in by_gate and by_gate[gate_id]["standing"] == "UNKNOWN"
    )
    satisfied = sorted(
        gate_id
        for gate_id in required
        if gate_id in by_gate and by_gate[gate_id]["standing"] == "SATISFIED"
    )
    unresolved = sorted(contract["unresolvedAssumptions"])

    if unsatisfied:
        standing = "SUCCESSOR_GATES_UNSATISFIED"
    elif missing or unknown or unresolved:
        standing = "SUCCESSOR_GATES_OPEN"
    else:
        standing = "SUCCESSOR_GATES_SATISFIED"

    projection: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.successor-gate-projection",
        "truthRole": "bounded-succession-gate-projection-not-promotion-verdict",
        "contractId": contract["contractId"],
        "contractDigest": compiled["contractDigest"],
        "predecessorRef": contract["predecessorRef"],
        "candidateRef": contract["candidateRef"],
        "standing": standing,
        "recursionClass": compiled["recursionClass"],
        "evaluationGroundingMode": compiled["evaluationGroundingMode"],
        "externallyGrounded": compiled["externallyGrounded"],
        "requiredGateIds": sorted(required),
        "satisfiedGateIds": satisfied,
        "unsatisfiedGateIds": unsatisfied,
        "unknownGateIds": unknown,
        "missingGateIds": missing,
        "unresolvedAssumptions": unresolved,
        "mechanicalSuccessorClosure": standing == "SUCCESSOR_GATES_SATISFIED",
        "promotionAuthorityEstablished": False,
        "domainImprovementEstablished": False,
        "claimBoundary": (
            "Mechanical successor closure means only that every required verifier-owned "
            "gate for this exact predecessor/candidate contract is SATISFIED and no "
            "contract assumption remains unresolved. Promotion authority and domain "
            "improvement remain with their natural owners."
        ),
    }
    projection["projectionDigest"] = canonical_digest(projection)
    return projection


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser("compile")
    compile_parser.add_argument("contract", type=Path)

    verify_parser = sub.add_parser("verify-gates")
    verify_parser.add_argument("contract", type=Path)
    verify_parser.add_argument("results", nargs="*", type=Path)

    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        contract = _load_json(args.contract)
        if args.command == "compile":
            output = compile_successor_contract(contract)
        else:
            results = [_load_json(path) for path in args.results]
            output = evaluate_successor_gates(contract, results)
    except (OSError, json.JSONDecodeError, CircuitContractError) as exc:
        raise SystemExit(f"successor contract R1 failed: {exc}") from exc
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
