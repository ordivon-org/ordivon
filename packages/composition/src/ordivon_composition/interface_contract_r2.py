#!/usr/bin/env python3
"""Interface Contract Evolution R2 mechanical evaluator.

R2 consumes already-observed interface identities and a caller-authored task-local
consumer expectation. It keeps compatibility, currentness, and evidence admissibility
orthogonal. It does not discover interfaces, refresh client catalogs, infer SemVer
compatibility, mint owner currentness, or establish domain success.
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
OBSERVATION_SCHEMA = ROOT / "schemas" / "interface-contract-observation-v1.schema.json"
EXPECTATION_SCHEMA = ROOT / "schemas" / "interface-contract-expectation-v1.schema.json"
RESULT_SCHEMA = ROOT / "schemas" / "interface-compatibility-result-v1.schema.json"


def currentness_standing(observation: dict[str, Any]) -> str:
    source_kind = observation["sourceKind"]
    if source_kind in {"direct-owner-observation", "client-effective-surface"}:
        return "POINT_IN_TIME_OBSERVED"

    projected = observation["projectedAuthorityVersionRef"]
    live = observation["liveAuthorityVersionRef"]
    if live is None:
        return "CURRENTNESS_UNKNOWN"
    if projected == live:
        return "CURRENT_DECLARED"
    return "HISTORICAL_NOT_CURRENT"


def _compatibility(
    observation: dict[str, Any],
    expectation: dict[str, Any],
) -> tuple[str, str, list[str]]:
    observed_ref = observation["interfaceRef"]
    evidence: list[str] = [observation["sourceRef"]]

    if observed_ref["id"] != expectation["interfaceId"]:
        return "MISMATCH", "INTERFACE_ID_MISMATCH", evidence
    if observed_ref["digest"] == expectation["requiredDigest"]:
        return "EXACT_MATCH", "EXACT_DIGEST_MATCH", evidence

    accepted = {
        item["digest"]: item["compatibilityEvidenceRef"]
        for item in expectation["acceptedAlternates"]
    }
    compatibility_ref = accepted.get(observed_ref["digest"])
    if compatibility_ref is not None:
        evidence.append(compatibility_ref)
        return (
            "COMPATIBLE_BY_DECLARATION",
            "EXPLICIT_ALTERNATE_ACCEPTED",
            evidence,
        )
    return "MISMATCH", "INTERFACE_DIGEST_NOT_ACCEPTED", evidence


def _admissibility(
    *,
    source_kind: str,
    accepted_source_kinds: list[str],
    compatibility_standing: str,
    currentness: str,
) -> tuple[str, str]:
    if source_kind not in accepted_source_kinds:
        return "INADMISSIBLE", "SOURCE_KIND_NOT_ACCEPTED"
    if compatibility_standing == "MISMATCH":
        return "INADMISSIBLE", "INTERFACE_MISMATCH"
    if currentness == "HISTORICAL_NOT_CURRENT":
        return "INADMISSIBLE", "OBSERVATION_HISTORICAL"
    if currentness == "CURRENTNESS_UNKNOWN":
        return "UNKNOWN", "CURRENTNESS_UNKNOWN"
    if currentness == "CURRENT_DECLARED":
        return "ADMISSIBLE", "ACCEPTED_CURRENT_DECLARED"
    return "ADMISSIBLE", "ACCEPTED_POINT_IN_TIME"


def evaluate_interface(
    observation: dict[str, Any],
    expectation: dict[str, Any],
) -> dict[str, Any]:
    _validate_schema(observation, OBSERVATION_SCHEMA, "interface observation")
    _validate_schema(expectation, EXPECTATION_SCHEMA, "interface expectation")

    alternate_digests = [item["digest"] for item in expectation["acceptedAlternates"]]
    if len(alternate_digests) != len(set(alternate_digests)):
        raise CircuitContractError("duplicate accepted alternate interface digest")

    observation_circuit_ref = dict(observation["circuitRef"])
    expectation_circuit_ref = dict(expectation["circuitRef"])
    if observation_circuit_ref != expectation_circuit_ref:
        raise CircuitContractError("observation and expectation circuitRef mismatch")

    obs_digest = canonical_digest(observation)
    exp_digest = canonical_digest(expectation)
    observed_ref = dict(observation["interfaceRef"])
    expected_ref = {
        "id": expectation["interfaceId"],
        "digest": expectation["requiredDigest"],
    }

    compatibility_standing, compatibility_reason, evidence = _compatibility(
        observation,
        expectation,
    )
    currentness = currentness_standing(observation)
    admissibility, admissibility_reason = _admissibility(
        source_kind=observation["sourceKind"],
        accepted_source_kinds=expectation["acceptedSourceKinds"],
        compatibility_standing=compatibility_standing,
        currentness=currentness,
    )

    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.interface-compatibility-result",
        "circuitRef": expectation_circuit_ref,
        "observationDigest": obs_digest,
        "expectationDigest": exp_digest,
        "observedInterfaceRef": observed_ref,
        "expectedInterfaceRef": expected_ref,
        "compatibilityStanding": compatibility_standing,
        "compatibilityReasonCode": compatibility_reason,
        "currentnessStanding": currentness,
        "evidenceAdmissibility": admissibility,
        "admissibilityReasonCode": admissibility_reason,
        "evidenceRefs": sorted(set(evidence)),
        "supportScope": expectation["supportScope"],
        "domainAcceptanceEstablished": False,
        "claimBoundary": (
            "This result classifies only the named task-local interface seam against "
            "the exact circuit-bound observation and expectation. Compatibility, "
            "currentness, and evidence admissibility remain distinct. Point-in-time "
            "admissibility is not durable freshness. The result does not refresh "
            "catalogs, mint owner authority, infer compatibility outside explicit "
            "declarations, or establish domain acceptance."
        ),
    }
    result_digest = canonical_digest(result)
    result["resultDigest"] = result_digest
    result["evidenceRef"] = f"interface-compatibility:{result_digest}"
    _validate_schema(result, RESULT_SCHEMA, "interface compatibility result")
    return result


# This is a strict R2.1 *declaration* admission boundary, not a proof checker.
# Keep historical interface compatibility and structural circuit projections
# unchanged: their callers have not asserted formal LEGO qualification.
R21_COORDINATES = ("I", "O", "S", "pre", "post", "inv", "eff", "c", "epsilon", "prov", "unfold")
R21_CONTEXT = (
    "id",
    "responsibility",
    "goal",
    "consumerRef",
    "semanticProfile",
    "behavioralContract",
    "representation",
    "observationBoundary",
    "acceptance",
)


def _meaningful_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value != "UNKNOWN"


def _semantic_coordinate_valid(key: str, value: Any) -> bool:
    if key == "unfold":
        return isinstance(value, list) and all(_meaningful_text(item) for item in value)
    if not isinstance(value, dict) or not value:
        return False
    if key in {"I", "O", "S"}:
        return _meaningful_text(value.get("type")) and _meaningful_text(value.get("meaning"))
    if key in {"pre", "post", "inv"}:
        return _meaningful_text(value.get("predicate"))
    if key == "eff":
        return _meaningful_text(value.get("kind")) and _meaningful_text(value.get("assumption"))
    if key == "c":
        return (
            value.get("standing") in {"UNKNOWN", "MEASURED", "BOUNDED"}
            and _meaningful_text(value.get("metric"))
            and (
                value["standing"] == "UNKNOWN"
                or isinstance(value.get("value"), (str, int, float))
                and not isinstance(value.get("value"), bool)
            )
        )
    if key == "epsilon":
        if not _meaningful_text(value.get("standing")):
            return False
        if value["standing"] == "EXACT_DECLARED":
            return isinstance(value.get("value"), str) and bool(value["value"].strip())
        return value["standing"] == "UNMEASURED" and _meaningful_text(value.get("reason"))
    if key == "prov":
        return _meaningful_text(value.get("sourceCut")) and _meaningful_text(value.get("specRef"))
    return False


def inspect_lego_declaration(declaration: dict[str, Any]) -> dict[str, Any]:
    """Classify one mandatory full R2.1 tuple; never self-issue Formal PASS.

    This validates *declared shape* only. The selected behavioral semantics,
    type soundness, nonvacuity and implementation relation require independent
    qualified verification at the natural owner. Untrusted proof fields cannot
    promote a declaration to a checked theorem.
    """
    if not isinstance(declaration, dict):
        raise CircuitContractError("R2.1 declaration must be an object")

    required = (*R21_CONTEXT, *R21_COORDINATES)
    missing = [key for key in required if key not in declaration]
    invalid = []
    for key in required:
        if key not in declaration:
            continue
        value = declaration[key]
        if key == "acceptance":
            valid = isinstance(value, dict) and _meaningful_text(value.get("criterion"))
        elif key == "behavioralContract":
            valid = isinstance(value, dict) and all(
                isinstance(value.get(name), dict) and _meaningful_text(value[name].get("predicate"))
                for name in ("assumption", "guarantee", "totality")
            )
        elif key == "representation":
            valid = isinstance(value, dict) and all(
                _meaningful_text(value.get(name)) for name in ("relation", "concreteWitness")
            )
        elif key == "observationBoundary":
            valid = (
                isinstance(value, dict)
                and _meaningful_text(value.get("scope"))
                and isinstance(value.get("outputs"), list)
                and bool(value["outputs"])
                and all(_meaningful_text(item) for item in value["outputs"])
                and isinstance(value.get("effects"), list)
                and all(_meaningful_text(item) for item in value["effects"])
            )
        elif key in R21_CONTEXT:
            valid = _meaningful_text(value)
        else:
            valid = _semantic_coordinate_valid(key, value)
        if not valid:
            invalid.append(key)

    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.r21-lego-declaration-inspection",
        "declarationDigest": canonical_digest(declaration),
        "declarationStanding": (
            "DECLARATION_COMPLETE_UNPROVED"
            if not missing and not invalid
            else "CANDIDATE_UNQUALIFIED"
        ),
        "missingCoordinates": missing,
        "invalidCoordinates": invalid,
        "modelProofStanding": "UNKNOWN",
        "implementationRefinement": "UNKNOWN",
        "installedCurrentness": "UNKNOWN",
        "promotionAdmissible": False,
        "truthBoundary": (
            "Complete declaration is not nonvacuous semantics, contract "
            "composition, a checker-issued mathematical proof, implementation "
            "refinement, owner authenticity, or installed currentness."
        ),
    }
    result["resultDigest"] = canonical_digest(result)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("observation", type=Path)
    evaluate.add_argument("expectation", type=Path)
    inspect = sub.add_parser("inspect-lego")
    inspect.add_argument("declaration", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "inspect-lego":
            result = inspect_lego_declaration(_load_json(args.declaration))
        else:
            result = evaluate_interface(
                _load_json(args.observation),
                _load_json(args.expectation),
            )
    except (OSError, json.JSONDecodeError, CircuitContractError) as exc:
        raise SystemExit(f"interface contract R2 failed: {exc}") from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
