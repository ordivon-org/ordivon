#!/usr/bin/env python3
"""Pacti shadow dogfood through Verification Obligation R1.

This script is intentionally not part of default project dependencies. Run it in an
ephemeral environment with exact pacti==0.3.1. It proves only algebraic compatibility of
the frozen timeout seam model and exercises the task-local obligation/binding thin waist.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ordivon_composition import (
    CircuitContractError,
    canonical_digest,
    compile_verification_obligations,
    evaluate_gate_results,
    resolve_verifier_bindings,
    validate_gate_result,
    validate_manifest,
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CircuitContractError(f"{path}: root must be an object")
    return value


def validate_spec(spec: dict[str, Any]) -> None:
    if spec.get("schemaVersion") != 1:
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
        if not isinstance(grant, int) or grant < 1:
            raise CircuitContractError(f"{key}.grantMaxMs must be a positive integer")
        if not isinstance(runtime, int) or runtime < 1:
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


def _contract_bundle(grant_max_ms: int, runtime_max_ms: int):
    try:
        import pacti
        from pacti.contracts import PolyhedralIoContract as Contract
    except ModuleNotFoundError as exc:
        raise CircuitContractError(
            "Pacti is not installed; run with uv --isolated --with pacti==0.3.1"
        ) from exc

    version = getattr(pacti, "__version__", None)
    if version != "0.3.1":
        raise CircuitContractError(f"unexpected Pacti version: {version}")

    grant = Contract.from_strings(
        [],
        ["t_grant >= 1", f"t_grant <= {grant_max_ms}"],
        [],
        ["t_grant"],
    )
    gateway = Contract.from_strings(
        [],
        ["t_gateway - t_grant = 0"],
        ["t_grant"],
        ["t_gateway"],
    )
    runtime = Contract.from_strings(
        ["t_gateway >= 1", f"t_gateway <= {runtime_max_ms}"],
        ["t_runtime - t_gateway = 0"],
        ["t_gateway"],
        ["t_runtime"],
    )
    top = Contract.from_strings(
        [],
        ["t_runtime >= 1", f"t_runtime <= {grant_max_ms}"],
        [],
        ["t_runtime"],
    )
    return grant, gateway, runtime, top


def execute_pacti(spec: dict[str, Any]) -> dict[str, Any]:
    validate_spec(spec)
    accepted = spec["acceptedCase"]
    grant, gateway, runtime, top = _contract_bundle(
        accepted["grantMaxMs"],
        accepted["runtimeMaxMs"],
    )
    known = grant.compose(gateway)
    composed = known.compose(runtime)
    accepted_refines = composed.refines(top)

    quotient = top.quotient(known)
    quotient_recomposes = known.compose(quotient).refines(top)

    mismatch = spec["deliberateMismatch"]
    bad_grant, bad_gateway, bad_runtime, _ = _contract_bundle(
        mismatch["grantMaxMs"],
        mismatch["runtimeMaxMs"],
    )
    mismatch_error_type: str | None = None
    mismatch_error: str | None = None
    try:
        bad_grant.compose(bad_gateway).compose(bad_runtime)
    except Exception as exc:  # Pacti owns the concrete exception hierarchy.
        mismatch_error_type = type(exc).__name__
        mismatch_error = str(exc)

    formal = {
        "pactiVersion": spec["pactiVersion"],
        "acceptedCase": {
            "grantMaxMs": accepted["grantMaxMs"],
            "runtimeMaxMs": accepted["runtimeMaxMs"],
            "composedContract": composed.to_dict(),
            "refinesTopRequirement": accepted_refines,
        },
        "quotient": {
            "contract": quotient.to_dict(),
            "recomposedRefinesTopRequirement": quotient_recomposes,
        },
        "deliberateMismatch": {
            "grantMaxMs": mismatch["grantMaxMs"],
            "runtimeMaxMs": mismatch["runtimeMaxMs"],
            "errorType": mismatch_error_type,
            "error": mismatch_error,
            "rejected": mismatch_error_type == "IncompatibleArgsError",
        },
    }
    formal["formalResultDigest"] = canonical_digest(formal)
    return formal


def run(spec: dict[str, Any]) -> dict[str, Any]:
    manifest = build_manifest(spec)
    obligations = compile_verification_obligations(manifest)
    bindings = build_binding_set(obligations, spec)
    resolution = resolve_verifier_bindings(obligations, bindings)
    formal = execute_pacti(spec)

    accepted = formal["acceptedCase"]["refinesTopRequirement"]
    quotient = formal["quotient"]["recomposedRefinesTopRequirement"]
    mismatch = formal["deliberateMismatch"]["rejected"]
    standing = "SATISFIED" if accepted and quotient and mismatch else "UNSATISFIED"

    gate = manifest["gateRequirements"][0]
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.composition-gate-result",
        "circuitId": manifest["circuitId"],
        "manifestDigest": obligations["circuitRef"]["digest"],
        "gateId": gate["id"],
        "verifierOwnerId": gate["verifierOwnerId"],
        "standing": standing,
        "evidenceRefs": [
            f"pacti-provider:{bindings['bindings'][0]['verifierRef']['digest']}",
            f"pacti-spec:{canonical_digest(spec)}",
            f"pacti-run:{formal['formalResultDigest']}",
        ],
        "supportScope": gate["supportScope"],
        "nonClaims": [
            "Pacti PASS establishes only the frozen algebraic contract relation.",
            "Pacti PASS does not prove Gateway or Runtime implementation conformance.",
            "Pacti PASS does not grant execution authority or establish domain acceptance.",
        ],
    }
    from ordivon_composition import compile_manifest

    validate_gate_result(manifest, compile_manifest(manifest), result)
    projection = evaluate_gate_results(manifest, [result])

    output = {
        "schemaVersion": 1,
        "kind": "ordivon.verification-obligation-pacti-shadow-r2",
        "specRef": {
            "id": spec["id"],
            "digest": canonical_digest(spec),
        },
        "obligationSet": obligations,
        "bindingSet": bindings,
        "resolution": resolution,
        "formalResult": formal,
        "gateResult": result,
        "projection": projection,
        "nonClaims": list(spec["nonClaims"]),
    }
    output["resultDigest"] = canonical_digest(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    args = parser.parse_args()
    try:
        result = run(_load(args.spec))
    except (OSError, json.JSONDecodeError, CircuitContractError) as exc:
        raise SystemExit(f"Pacti timeout obligation R2 failed: {exc}") from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
