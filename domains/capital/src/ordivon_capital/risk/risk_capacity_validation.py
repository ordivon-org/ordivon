from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Any

RISK_CAPACITY_SCHEMA_SHA256 = "58e43a8da7eed77e1cd1a4b0bdd98a03d6d0129c3f6caef818cbeede7c0ee6af"
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")
_STANDINGS = {"SUPPORTED", "CONSTRAINED", "INSUFFICIENT", "UNKNOWN"}
_RELATIONS = {"MAX", "MIN", "REQUIRE", "PROHIBIT"}


class RiskCapacityValidationError(ValueError):
    """Validation failure for the exact Capital R3 risk-capacity v1 contract."""


def assert_risk_capacity_schema_identity(schema_path: Path) -> None:
    digest = hashlib.sha256(schema_path.read_bytes()).hexdigest()
    if digest != RISK_CAPACITY_SCHEMA_SHA256:
        raise RiskCapacityValidationError(
            "risk capacity schema changed; requalification required"
        )


def _exact_object(
    value: Any,
    *,
    label: str,
    required: set[str],
    optional: set[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RiskCapacityValidationError(f"{label} must be an object")
    optional = optional or set()
    keys = set(value)
    missing = required - keys
    extra = keys - required - optional
    if missing or extra:
        raise RiskCapacityValidationError(
            f"{label} keys mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )
    return value


def _nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RiskCapacityValidationError(f"{label} must be a non-empty string")
    return value


def _identifier(value: Any, label: str) -> str:
    text = _nonempty_string(value, label)
    if not _IDENTIFIER.fullmatch(text):
        raise RiskCapacityValidationError(f"{label} is not a valid identifier")
    return text


def _digest(value: Any, label: str) -> str:
    text = _nonempty_string(value, label)
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", text):
        raise RiskCapacityValidationError(f"{label} must be a sha256 digest")
    return text


def _datetime(value: Any, label: str) -> str:
    text = _nonempty_string(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RiskCapacityValidationError(f"{label} must be an RFC3339 date-time") from exc
    if parsed.tzinfo is None:
        raise RiskCapacityValidationError(f"{label} must include a timezone")
    return text


def validate_risk_capacity_document(doc: Any) -> dict[str, Any]:
    required = {
        "schemaVersion",
        "kind",
        "capacityId",
        "asOf",
        "scope",
        "standing",
        "evidenceClaims",
        "capacityConstraints",
        "riskAppetiteInferred",
        "riskBudgetGranted",
        "externalEffectAuthorityGranted",
    }
    root = _exact_object(
        doc,
        label="risk capacity",
        required=required,
        optional={"notes"},
    )
    if root["schemaVersion"] != 1 or isinstance(root["schemaVersion"], bool):
        raise RiskCapacityValidationError("schemaVersion must equal 1")
    if root["kind"] != "ordivon.capital.risk-capacity":
        raise RiskCapacityValidationError("unexpected risk capacity kind")
    _identifier(root["capacityId"], "capacityId")
    _datetime(root["asOf"], "asOf")
    _nonempty_string(root["scope"], "scope")
    if root["standing"] not in _STANDINGS:
        raise RiskCapacityValidationError("invalid risk capacity standing")
    if root["riskAppetiteInferred"] is not False:
        raise RiskCapacityValidationError("risk capacity cannot infer owner risk appetite")
    if root["riskBudgetGranted"] is not False:
        raise RiskCapacityValidationError("risk capacity cannot grant a risk budget")
    if root["externalEffectAuthorityGranted"] is not False:
        raise RiskCapacityValidationError("risk capacity cannot grant external effect authority")
    if "notes" in root and not isinstance(root["notes"], str):
        raise RiskCapacityValidationError("notes must be a string")

    claims = root["evidenceClaims"]
    if not isinstance(claims, list):
        raise RiskCapacityValidationError("evidenceClaims must be an array")
    for index, claim in enumerate(claims):
        row = _exact_object(
            claim,
            label=f"evidenceClaims[{index}]",
            required={"claimId", "producer", "observedAt", "validUntil", "evidenceDigest"},
        )
        _identifier(row["claimId"], f"evidenceClaims[{index}].claimId")
        _nonempty_string(row["producer"], f"evidenceClaims[{index}].producer")
        _datetime(row["observedAt"], f"evidenceClaims[{index}].observedAt")
        _datetime(row["validUntil"], f"evidenceClaims[{index}].validUntil")
        _digest(row["evidenceDigest"], f"evidenceClaims[{index}].evidenceDigest")

    constraints = root["capacityConstraints"]
    if not isinstance(constraints, list):
        raise RiskCapacityValidationError("capacityConstraints must be an array")
    for index, constraint in enumerate(constraints):
        row = _exact_object(
            constraint,
            label=f"capacityConstraints[{index}]",
            required={
                "constraintId",
                "dimension",
                "relation",
                "value",
                "unit",
                "authorityRole",
            },
        )
        _identifier(row["constraintId"], f"capacityConstraints[{index}].constraintId")
        _nonempty_string(row["dimension"], f"capacityConstraints[{index}].dimension")
        if row["relation"] not in _RELATIONS:
            raise RiskCapacityValidationError(
                f"capacityConstraints[{index}].relation is invalid"
            )
        value = row["value"]
        if not isinstance(value, (str, int, float, bool)):
            raise RiskCapacityValidationError(
                f"capacityConstraints[{index}].value has invalid type"
            )
        _nonempty_string(row["unit"], f"capacityConstraints[{index}].unit")
        if row["authorityRole"] != "SAFETY_ENVELOPE_ONLY":
            raise RiskCapacityValidationError(
                f"capacityConstraints[{index}].authorityRole must be SAFETY_ENVELOPE_ONLY"
            )
    return root
