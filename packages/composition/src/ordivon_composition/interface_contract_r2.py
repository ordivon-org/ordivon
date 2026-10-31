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


LEGO_DECLARATION_SCHEMA = ROOT / "schemas" / "lego-declaration-r21.schema.json"
LEGO_COORDINATES = ("I", "O", "S", "pre", "post", "inv", "eff", "c", "epsilon", "prov", "unfold")


def inspect_lego_declaration(declaration: dict[str, Any]) -> dict[str, Any]:
    """Check only complete R2.1 declaration shape, not proof or permission."""
    _validate_schema(declaration, LEGO_DECLARATION_SCHEMA, "R2.1 LEGO declaration")
    for name in (
        "identity",
        "responsibility",
        "goal",
        "consumerRef",
        "semanticProfile",
        "publicObservation",
        "sourceRef",
    ):
        if not declaration[name].strip():
            raise CircuitContractError(f"R2.1 {name} cannot be whitespace")
    for name in ("criterion", "baseline", "oracle"):
        if not declaration["acceptance"][name].strip():
            raise CircuitContractError(f"R2.1 acceptance.{name} cannot be whitespace")
    unknown_coordinates: list[str] = []
    for name in LEGO_COORDINATES:
        cell = declaration["ell"][name]
        if not cell["type"].strip():
            raise CircuitContractError(f"R2.1 {name} type cannot be whitespace")
        if cell["standing"] == "UNKNOWN":
            if not cell["reason"].strip():
                raise CircuitContractError(f"R2.1 {name} UNKNOWN needs a reason")
            unknown_coordinates.append(name)
        elif not cell["statement"].strip() or cell["statement"].strip().upper() == "UNKNOWN":
            raise CircuitContractError(f"R2.1 {name} DECLARED needs a concrete statement")
    return {
        "kind": "ordivon.r21.lego-declaration-inspection",
        "identity": declaration["identity"],
        "declarationDigest": canonical_digest(declaration),
        "declarationStanding": (
            "DECLARATION_COMPLETE_WITH_UNKNOWNS"
            if unknown_coordinates
            else "DECLARATION_COMPLETE_UNPROVED"
        ),
        "unknownCoordinates": unknown_coordinates,
        "semanticProfile": declaration["semanticProfile"],
        "consumerRef": declaration["consumerRef"],
        "publicInfo": {
            "goal": declaration["goal"],
            "responsibility": declaration["responsibility"],
            "publicObservation": declaration["publicObservation"],
            "types": {
                name: declaration["ell"][name]
                for name in ("I", "O", "pre", "post", "inv", "eff", "c", "epsilon")
            },
            "sourceRef": declaration["sourceRef"],
            "acceptance": declaration["acceptance"],
        },
        "nonvacuityEstablished": False,
        "modelProofEstablished": False,
        "implementationRefined": False,
        "installedCurrent": False,
        "consumerObserved": False,
        "safeToInvoke": False,
        "domainAcceptanceEstablished": False,
        "claimBoundary": (
            "Only caller-declared shape is checked. No satisfiability, "
            "nonvacuity, profile soundness, source authenticity/refinement, "
            "authorization, installation, consumer use or domain completion."
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("observation", type=Path)
    evaluate.add_argument("expectation", type=Path)
    qualify = sub.add_parser("qualify")
    qualify.add_argument("declaration", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "qualify":
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
