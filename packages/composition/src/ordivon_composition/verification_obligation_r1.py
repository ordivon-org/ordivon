#!/usr/bin/env python3
"""Task-local verification-obligation compilation and verifier-binding resolution.

R1 deliberately compiles only existing Cognitive Circuit composition gates. It does not
invent domain properties, discover verifiers, rank providers, execute verification, grant
authority, or establish domain completion. Caller-authored task-local bindings identify the
verifier/provider that will discharge each obligation through the existing Composition Gate
result contract.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .cognitive_circuit_r1 import (
    CircuitContractError,
    canonical_digest,
    compile_manifest,
)

ROOT = Path(__file__).resolve().parent
OBLIGATION_SET_SCHEMA = ROOT / "schemas" / "verification-obligation-set-v1.schema.json"
BINDING_SET_SCHEMA = ROOT / "schemas" / "verifier-binding-set-v1.schema.json"
RESOLUTION_SCHEMA = ROOT / "schemas" / "verifier-resolution-v1.schema.json"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CircuitContractError(f"{path}: root must be an object")
    return value


def _schema(path: Path) -> dict[str, Any]:
    return _load_json(path)


def _validate_schema(value: dict[str, Any], schema_path: Path, label: str) -> None:
    validator = Draft202012Validator(_schema(schema_path))
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
    if errors:
        first = errors[0]
        location = "/".join(str(item) for item in first.absolute_path) or "<root>"
        raise CircuitContractError(f"{label} schema violation at {location}: {first.message}")


def _unique_by(rows: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = row[key]
        if row_id in result:
            raise CircuitContractError(f"duplicate {label}: {row_id}")
        result[row_id] = row
    return result


def _obligation_from_gate(
    *,
    circuit_ref: dict[str, str],
    gate: dict[str, Any],
) -> dict[str, Any]:
    obligation: dict[str, Any] = {
        "gateId": gate["id"],
        "sourceGateDigest": canonical_digest(gate),
        "circuitRef": dict(circuit_ref),
        "producerStageId": gate["producerStageId"],
        "consumerStageId": gate["consumerStageId"],
        "assumption": gate["assumption"],
        "guarantee": gate["guarantee"],
        "verifierOwnerId": gate["verifierOwnerId"],
        "supportScope": gate["supportScope"],
        "required": gate["required"],
        "requiredStanding": "SATISFIED",
        "resultKind": "ordivon.composition-gate-result",
        "nonClaims": [
            "This obligation is a task-local projection of an existing Composition Gate.",
            "Discharging it establishes only the named support scope, not domain acceptance.",
        ],
    }
    obligation["obligationDigest"] = canonical_digest(obligation)
    return obligation


def compile_verification_obligations(manifest: dict[str, Any]) -> dict[str, Any]:
    """Compile R1 Composition Gates into exact task-local verification obligations."""

    compiled = compile_manifest(manifest)
    circuit_ref = {
        "id": manifest["circuitId"],
        "digest": compiled["manifestDigest"],
    }
    obligations = [
        _obligation_from_gate(circuit_ref=circuit_ref, gate=gate)
        for gate in sorted(manifest["gateRequirements"], key=lambda item: item["id"])
    ]
    projection: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.verification-obligation-set",
        "truthRole": "task-local-non-authoritative-verification-obligation-projection",
        "circuitRef": circuit_ref,
        "obligations": obligations,
        "requiredGateIds": sorted(
            obligation["gateId"] for obligation in obligations if obligation["required"]
        ),
        "nonClaims": [
            "This projection does not discover, select, rank, or execute verifiers.",
            "This projection grants no Tool, credential, workflow, retry, or domain authority.",
            "Verification closure does not establish domain acceptance.",
        ],
    }
    projection["obligationSetDigest"] = canonical_digest(projection)
    _validate_schema(projection, OBLIGATION_SET_SCHEMA, "verification obligation set")
    return projection


def validate_obligation_set(value: dict[str, Any]) -> None:
    _validate_schema(value, OBLIGATION_SET_SCHEMA, "verification obligation set")
    obligations = _unique_by(value["obligations"], "gateId", "verification obligation gateId")

    expected_required = sorted(
        obligation["gateId"] for obligation in obligations.values() if obligation["required"]
    )
    if value["requiredGateIds"] != expected_required:
        raise CircuitContractError("verification obligation requiredGateIds mismatch")

    for obligation in obligations.values():
        embedded = obligation["obligationDigest"]
        base = dict(obligation)
        del base["obligationDigest"]
        if canonical_digest(base) != embedded:
            raise CircuitContractError(
                f"verification obligation digest mismatch: {obligation['gateId']}"
            )

    set_digest = value["obligationSetDigest"]
    base_set = dict(value)
    del base_set["obligationSetDigest"]
    if canonical_digest(base_set) != set_digest:
        raise CircuitContractError("verification obligation set digest mismatch")


def resolve_verifier_bindings(
    obligation_set: dict[str, Any],
    binding_set: dict[str, Any],
) -> dict[str, Any]:
    """Validate exact caller-authored verifier bindings against one obligation set.

    "Resolve" here means deterministic binding validation only. This function performs no
    registry lookup, provider discovery, availability probe, ranking, or verifier execution.
    """

    validate_obligation_set(obligation_set)
    _validate_schema(binding_set, BINDING_SET_SCHEMA, "verifier binding set")

    if binding_set["circuitRef"] != obligation_set["circuitRef"]:
        raise CircuitContractError("verifier binding set circuitRef mismatch")
    if binding_set["obligationSetDigest"] != obligation_set["obligationSetDigest"]:
        raise CircuitContractError("verifier binding set targets a stale/different obligation set")

    obligations = _unique_by(
        obligation_set["obligations"],
        "gateId",
        "verification obligation gateId",
    )
    bindings = _unique_by(binding_set["bindings"], "gateId", "verifier binding gateId")

    unknown = sorted(set(bindings) - set(obligations))
    if unknown:
        raise CircuitContractError(f"verifier bindings reference unknown obligations: {unknown}")

    resolved: list[dict[str, Any]] = []
    for gate_id in sorted(bindings):
        binding = bindings[gate_id]
        obligation = obligations[gate_id]
        if binding["obligationDigest"] != obligation["obligationDigest"]:
            raise CircuitContractError(f"verifier binding obligation digest mismatch: {gate_id}")
        if binding["verifierOwnerId"] != obligation["verifierOwnerId"]:
            raise CircuitContractError(f"verifier binding owner mismatch: {gate_id}")
        if binding["supportScope"] != obligation["supportScope"]:
            raise CircuitContractError(f"verifier binding support scope mismatch: {gate_id}")

        resolved.append(
            {
                "gateId": gate_id,
                "obligationDigest": obligation["obligationDigest"],
                "verifierOwnerId": binding["verifierOwnerId"],
                "verifierRef": dict(binding["verifierRef"]),
                "verifierClass": binding["verifierClass"],
                "nativeSpecificationRef": (
                    None
                    if binding["nativeSpecificationRef"] is None
                    else dict(binding["nativeSpecificationRef"])
                ),
                "supportScope": binding["supportScope"],
            }
        )

    missing_required = sorted(
        gate_id
        for gate_id, obligation in obligations.items()
        if obligation["required"] and gate_id not in bindings
    )
    unbound_optional = sorted(
        gate_id
        for gate_id, obligation in obligations.items()
        if not obligation["required"] and gate_id not in bindings
    )
    standing = "VERIFIER_BINDINGS_RESOLVED" if not missing_required else "VERIFIER_BINDINGS_OPEN"

    projection: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.verifier-resolution",
        "truthRole": "task-local-non-authoritative-verifier-binding-projection",
        "circuitRef": dict(obligation_set["circuitRef"]),
        "obligationSetDigest": obligation_set["obligationSetDigest"],
        "bindingSetDigest": canonical_digest(binding_set),
        "standing": standing,
        "resolvedBindings": resolved,
        "missingRequiredGateIds": missing_required,
        "unboundOptionalGateIds": unbound_optional,
        "mechanicalResolution": not missing_required,
        "executionAuthorityGranted": False,
        "domainAcceptanceEstablished": False,
        "claimBoundary": (
            "Resolution means only that every required task-local obligation has an exact "
            "caller-authored verifier binding whose owner, obligation digest, and support "
            "scope match. It does not prove verifier availability, execute verification, "
            "grant authority, discharge a gate, or establish domain acceptance."
        ),
    }
    projection["resolutionDigest"] = canonical_digest(projection)
    _validate_schema(projection, RESOLUTION_SCHEMA, "verifier resolution")
    return projection


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser("compile-obligations")
    compile_parser.add_argument("manifest", type=Path)

    resolve_parser = sub.add_parser("resolve-bindings")
    resolve_parser.add_argument("obligation_set", type=Path)
    resolve_parser.add_argument("binding_set", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "compile-obligations":
            result = compile_verification_obligations(_load_json(args.manifest))
        else:
            result = resolve_verifier_bindings(
                _load_json(args.obligation_set),
                _load_json(args.binding_set),
            )
    except (OSError, json.JSONDecodeError, CircuitContractError) as exc:
        raise SystemExit(f"verification obligation R1 failed: {exc}") from exc

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
