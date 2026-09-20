from __future__ import annotations

from typing import Any

OPERATION_KIND = "ordivon.artifact-operation"
OPERATION_KINDS = frozenset({"prepare", "build", "verify", "verify-trust", "package"})


def require_public_file_commitment(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    unknown = set(value) - {"path", "sha256", "name", "size"}
    if unknown:
        raise ValueError(f"{label} contains unsupported fields: {sorted(unknown)}")
    if not isinstance(value.get("path"), str) or not value["path"]:
        raise ValueError(f"{label}.path is required")
    digest = value.get("sha256")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(ch not in "0123456789abcdef" for ch in digest)
    ):
        raise ValueError(f"{label}.sha256 must be a lowercase SHA-256 hex digest")
    if value.get("name") is not None and not isinstance(value["name"], str):
        raise ValueError(f"{label}.name must be a string when present")
    if value.get("size") is not None and (
        not isinstance(value["size"], int) or value["size"] < 0
    ):
        raise ValueError(f"{label}.size must be a non-negative integer when present")
    return value


def validate_public_trust_material_envelope(value: object) -> dict[str, Any]:
    """Validate public verification material before it can enter durable history."""
    if not isinstance(value, dict):
        raise ValueError("trust material must be an object")
    allowed = {"trustPolicy", "bundles", "signerIds"}
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(f"trust material contains unsupported fields: {sorted(unknown)}")
    if set(value) != allowed:
        raise ValueError(
            "trust material requires exactly trustPolicy, bundles and signerIds"
        )
    require_public_file_commitment(value["trustPolicy"], "trustPolicy")
    bundles = value["bundles"]
    signer_ids = value["signerIds"]
    if not isinstance(bundles, dict) or not bundles:
        raise ValueError("trust material bundles must be a non-empty object")
    if not isinstance(signer_ids, dict) or set(signer_ids) != set(bundles):
        raise ValueError("trust material signerIds must exactly match bundle gates")
    for gate, fact in bundles.items():
        if not isinstance(gate, str) or not gate:
            raise ValueError(
                "trust material bundle gate names must be non-empty strings"
            )
        require_public_file_commitment(fact, f"bundles.{gate}")
        signer = signer_ids[gate]
        if not isinstance(signer, str) or not signer:
            raise ValueError(f"signerIds.{gate} must be a non-empty string")
    return value


def operation_envelope(
    operation_id: str,
    operation_kind: str,
    inputs: dict[str, Any],
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = {
        "schemaVersion": 1,
        "kind": OPERATION_KIND,
        "operationId": operation_id,
        "operationKind": operation_kind,
        "inputs": inputs,
        "options": options or {},
    }
    return validate_operation_envelope(value)


def validate_operation_envelope(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Artifact operation must be an object")
    allowed = {
        "schemaVersion",
        "kind",
        "operationId",
        "operationKind",
        "inputs",
        "options",
    }
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(f"Artifact operation contains unsupported fields: {sorted(unknown)}")
    if value.get("schemaVersion") != 1:
        raise ValueError("Artifact operation schemaVersion must equal 1")
    if value.get("kind") != OPERATION_KIND:
        raise ValueError(f"Artifact operation kind must equal {OPERATION_KIND}")
    operation_id = value.get("operationId")
    if not isinstance(operation_id, str) or not operation_id:
        raise ValueError("Artifact operation operationId is required")
    operation_kind = value.get("operationKind")
    if operation_kind not in OPERATION_KINDS:
        raise ValueError(f"unsupported Artifact operation kind: {operation_kind!r}")
    if not isinstance(value.get("inputs"), dict):
        raise ValueError("Artifact operation inputs must be an object")
    if not isinstance(value.get("options"), dict):
        raise ValueError("Artifact operation options must be an object")
    return value
