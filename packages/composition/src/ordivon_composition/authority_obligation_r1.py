"""Task-local authority-obligation compilation for exact Cognitive Circuit bindings.

Composition validates explicit caller-authored requirements against one exact Circuit. It
does not infer effect-bearing nodes, classify effects, discover authority owners, evaluate
policy, mint grants, validate credentials, or establish execution authority.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .cognitive_circuit_r1 import CircuitContractError, canonical_digest, compile_manifest

ROOT = Path(__file__).resolve().parent
REQUIREMENT_SET_SCHEMA = ROOT / "schemas" / "authority-requirement-set-v1.schema.json"
OBLIGATION_SET_SCHEMA = ROOT / "schemas" / "authority-obligation-set-v1.schema.json"


class AuthorityObligationError(CircuitContractError):
    """Machine-classified authority-obligation binding error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _load_schema(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AuthorityObligationError("INVALID_SCHEMA", f"{path}: schema root must be object")
    return value


def _validate_schema(value: dict[str, Any], path: Path, label: str) -> None:
    errors = sorted(
        Draft202012Validator(_load_schema(path)).iter_errors(value),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        first = errors[0]
        location = "/".join(str(item) for item in first.absolute_path) or "<root>"
        raise AuthorityObligationError(
            "INVALID_AUTHORITY_CONTRACT",
            f"{label} schema violation at {location}: {first.message}",
        )


def _unique_requirements(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = row["id"]
        if row_id in result:
            raise AuthorityObligationError(
                "DUPLICATE_AUTHORITY_REQUIREMENT",
                f"duplicate authority requirement id: {row_id}",
            )
        result[row_id] = row
    return result


def _expected_circuit_ref(manifest: dict[str, Any]) -> dict[str, str]:
    compiled = compile_manifest(manifest)
    return {"id": manifest["circuitId"], "digest": compiled["manifestDigest"]}


def compile_authority_obligations(
    manifest: dict[str, Any],
    requirement_set: dict[str, Any],
) -> dict[str, Any]:
    """Bind explicit external-authority requirements to exact Circuit stage/capability refs."""

    circuit_ref = _expected_circuit_ref(manifest)
    _validate_schema(requirement_set, REQUIREMENT_SET_SCHEMA, "authority requirement set")
    if requirement_set["circuitRef"] != circuit_ref:
        raise AuthorityObligationError(
            "CIRCUIT_REF_MISMATCH",
            "authority requirement set targets a stale/different Cognitive Circuit",
        )

    requirements = _unique_requirements(requirement_set["requirements"])
    stages = {row["id"]: row for row in manifest["stages"]}
    capabilities = {row["id"]: row for row in manifest["capabilityBindings"]}

    obligations: list[dict[str, Any]] = []
    for requirement_id in sorted(requirements):
        requirement = requirements[requirement_id]
        stage = stages.get(requirement["stageId"])
        if stage is None:
            raise AuthorityObligationError(
                "UNKNOWN_STAGE",
                f"authority requirement {requirement_id} references unknown stage",
            )
        capability_binding = capabilities.get(requirement["capabilityBindingId"])
        if capability_binding is None:
            raise AuthorityObligationError(
                "UNKNOWN_CAPABILITY_BINDING",
                f"authority requirement {requirement_id} references unknown capability binding",
            )
        if requirement["capabilityBindingId"] not in stage["capabilityBindings"]:
            raise AuthorityObligationError(
                "CAPABILITY_NOT_BOUND_TO_STAGE",
                f"authority requirement {requirement_id} capability is not bound to its stage",
            )

        non_claims = sorted(
            set(
                [
                    *requirement["nonClaims"],
                    "This obligation records an external authority prerequisite; it is not an ALLOW decision or Grant.",
                    "Composition does not infer whether all effect-bearing Circuit stages have authority requirements.",
                ]
            )
        )
        obligation: dict[str, Any] = {
            "id": requirement_id,
            "sourceRequirementDigest": canonical_digest(requirement),
            "circuitRef": dict(circuit_ref),
            "stageId": requirement["stageId"],
            "capabilityBindingId": requirement["capabilityBindingId"],
            "capability": capability_binding["capability"],
            "capabilityOwnerId": capability_binding["ownerId"],
            "authorityOwnerId": requirement["authorityOwnerId"],
            "authorityContractRef": dict(requirement["authorityContractRef"]),
            "required": requirement["required"],
            "authorityGranted": False,
            "nonClaims": non_claims,
        }
        obligation["obligationDigest"] = canonical_digest(obligation)
        obligations.append(obligation)

    projection: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.authority-obligation-set",
        "truthRole": "task-local-non-authoritative-authority-obligation-projection",
        "circuitRef": circuit_ref,
        "obligations": obligations,
        "requiredObligationIds": sorted(
            obligation["id"] for obligation in obligations if obligation["required"]
        ),
        "mechanicalBindingEstablished": True,
        "effectCoverageEstablished": False,
        "authorityGranted": False,
        "executionAuthorityGranted": False,
        "nonClaims": [
            "This projection validates only caller-authored Circuit/stage/capability/authority-contract bindings.",
            "Composition does not discover effect-bearing nodes, authority owners, policies, Grants, credentials, or decisions.",
            "A mechanically valid authority-obligation set does not authorize execution.",
        ],
    }
    projection["obligationSetDigest"] = canonical_digest(projection)
    validate_authority_obligation_set(projection)
    return projection


def validate_authority_obligation_set(value: dict[str, Any]) -> None:
    """Validate deterministic digests and non-authority invariants of one compiled set."""

    _validate_schema(value, OBLIGATION_SET_SCHEMA, "authority obligation set")
    seen: set[str] = set()
    expected_required: list[str] = []
    for obligation in value["obligations"]:
        obligation_id = obligation["id"]
        if obligation_id in seen:
            raise AuthorityObligationError(
                "DUPLICATE_AUTHORITY_OBLIGATION",
                f"duplicate authority obligation id: {obligation_id}",
            )
        seen.add(obligation_id)
        if obligation["required"]:
            expected_required.append(obligation_id)
        embedded = obligation["obligationDigest"]
        base = dict(obligation)
        del base["obligationDigest"]
        if canonical_digest(base) != embedded:
            raise AuthorityObligationError(
                "AUTHORITY_OBLIGATION_DIGEST_MISMATCH",
                f"authority obligation digest mismatch: {obligation_id}",
            )

    if value["requiredObligationIds"] != sorted(expected_required):
        raise AuthorityObligationError(
            "REQUIRED_AUTHORITY_OBLIGATIONS_MISMATCH",
            "requiredObligationIds does not match required obligations",
        )

    embedded_set = value["obligationSetDigest"]
    base_set = dict(value)
    del base_set["obligationSetDigest"]
    if canonical_digest(base_set) != embedded_set:
        raise AuthorityObligationError(
            "AUTHORITY_OBLIGATION_SET_DIGEST_MISMATCH",
            "authority obligation set digest mismatch",
        )


__all__ = [
    "AuthorityObligationError",
    "compile_authority_obligations",
    "validate_authority_obligation_set",
]
