"""Pacti shadow verification representation: specification, circuit, bindings.

The model module composes existing Ordivon Composition contracts only.
It does not import or execute the optional Pacti solver, grant execution
authority, or claim implementation refinement.
"""

from __future__ import annotations

from typing import Any

from ordivon_composition import (
    CircuitContractError,
    canonical_digest,
    validate_manifest,
)


def validate_spec(spec: dict[str, Any]) -> None:
    if type(spec.get("schemaVersion")) is not int or spec["schemaVersion"] != 1:
        raise CircuitContractError("spec schemaVersion must equal 1")
    if spec.get("kind") != "ordivon.pacti-timeout-obligation-spec":
        raise CircuitContractError("spec kind is invalid")
    if not isinstance(spec.get("id"), str) or not spec["id"]:
        raise CircuitContractError("spec id is required")
    if spec.get("pactiVersion") != "0.3.1":
        raise CircuitContractError("R2 dogfood is pinned to pacti 0.3.1")
    for key in ("acceptedCase", "deliberateMismatch"):
        case = spec.get(key)
        if not isinstance(case, dict):
            raise CircuitContractError(f"{key} must be an object")
        grant = case.get("grantMaxMs")
        runtime = case.get("runtimeMaxMs")
        if type(grant) is not int or grant < 1:
            raise CircuitContractError(f"{key}.grantMaxMs must be a positive integer")
        if type(runtime) is not int or runtime < 1:
            raise CircuitContractError(f"{key}.runtimeMaxMs must be a positive integer")
    if spec["acceptedCase"]["grantMaxMs"] > spec["acceptedCase"]["runtimeMaxMs"]:
        raise CircuitContractError("acceptedCase must be algebraically admissible")
    if (
        spec["deliberateMismatch"]["grantMaxMs"]
        <= spec["deliberateMismatch"]["runtimeMaxMs"]
    ):
        raise CircuitContractError("deliberateMismatch must exceed the Runtime bound")
    if not isinstance(spec.get("supportScope"), str) or not spec["supportScope"]:
        raise CircuitContractError("supportScope is required")
    if not isinstance(spec.get("nonClaims"), list) or not spec["nonClaims"]:
        raise CircuitContractError("nonClaims are required")


def build_manifest(spec: dict[str, Any]) -> dict[str, Any]:
    validate_spec(spec)
    accepted = spec["acceptedCase"]
    objective_digest = canonical_digest(
        {
            "specId": spec["id"],
            "grantMaxMs": accepted["grantMaxMs"],
            "runtimeMaxMs": accepted["runtimeMaxMs"],
        }
    )
    manifest = {
        "schemaVersion": 1,
        "kind": "ordivon.cognitive-circuit-manifest",
        "circuitId": "circuit:pacti-timeout-obligation-r2",
        "objectiveRef": {
            "id": "objective:timeout-contract-compatibility",
            "digest": objective_digest,
        },
        "methodBindings": [],
        "capabilityBindings": [],
        "stages": [
            {
                "id": "stage:gateway-timeout-contract",
                "ownerId": "gateway",
                "responsibility": "Preserve the caller-granted timeout value.",
                "dependsOn": [],
                "methodBindings": [],
                "capabilityBindings": [],
                "inputs": ["caller-timeout"],
                "outputs": ["forwarded-timeout"],
            },
            {
                "id": "stage:runtime-timeout-contract",
                "ownerId": "runtime",
                "responsibility": "Admit forwarded timeout values within the Runtime bound.",
                "dependsOn": ["stage:gateway-timeout-contract"],
                "methodBindings": [],
                "capabilityBindings": [],
                "inputs": ["forwarded-timeout"],
                "outputs": ["admitted-timeout"],
            },
        ],
        "edges": [
            {
                "id": "edge:gateway-runtime-timeout",
                "from": {
                    "stageId": "stage:gateway-timeout-contract",
                    "port": "forwarded-timeout",
                },
                "to": {
                    "stageId": "stage:runtime-timeout-contract",
                    "port": "forwarded-timeout",
                },
                "contractRef": spec["id"],
            }
        ],
        "gateRequirements": [
            {
                "id": "gate:pacti-timeout-contract",
                "producerStageId": "stage:gateway-timeout-contract",
                "consumerStageId": "stage:runtime-timeout-contract",
                "assumption": (
                    "Runtime contract accepts the complete caller-granted timeout domain."
                ),
                "guarantee": (
                    "Gateway contract preserves caller timeout exactly through the seam."
                ),
                "verifierOwnerId": "next.formal-shadow",
                "supportScope": spec["supportScope"],
                "required": True,
            }
        ],
        "unresolvedAssumptions": [],
        "nonClaims": list(spec["nonClaims"]),
    }
    validate_manifest(manifest)
    return manifest


def build_binding_set(
    obligation_set: dict[str, Any],
    spec: dict[str, Any],
) -> dict[str, Any]:
    validate_spec(spec)
    obligation = obligation_set["obligations"][0]
    verifier_identity = {
        "project": "pacti-org/pacti",
        "package": "pacti",
        "version": spec["pactiVersion"],
    }
    return {
        "schemaVersion": 1,
        "kind": "ordivon.task-local-verifier-binding-set",
        "circuitRef": dict(obligation_set["circuitRef"]),
        "obligationSetDigest": obligation_set["obligationSetDigest"],
        "bindings": [
            {
                "gateId": obligation["gateId"],
                "obligationDigest": obligation["obligationDigest"],
                "verifierOwnerId": obligation["verifierOwnerId"],
                "verifierRef": {
                    "id": f"provider:pacti:{spec['pactiVersion']}",
                    "digest": canonical_digest(verifier_identity),
                },
                "verifierClass": "contract-algebra",
                "nativeSpecificationRef": {
                    "id": spec["id"],
                    "digest": canonical_digest(spec),
                },
                "supportScope": obligation["supportScope"],
                "nonClaims": [
                    "Pacti is a scoped algebra provider, not Ordivon domain truth."
                ],
            }
        ],
        "nonClaims": [
            "This task-local binding does not install or activate Pacti globally.",
            "Formal refinement does not establish implementation conformance.",
            "Binding resolution does not grant execution authority.",
        ],
    }
