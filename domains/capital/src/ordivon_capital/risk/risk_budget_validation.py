from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

RISK_BUDGET_SCHEMA_SHA256 = "adcb39da9dc367603935a44c3328516b2f108983c8f30dd23fbd2f4ed38f7d4e"
_LIMIT_KEYS = {
    "maxGrossToEquity",
    "maxLargestPositionGrossShare",
    "minAvailableEquityRatio",
    "shockMagnitudePct",
    "maxEquityLossPctAtShock",
}


class RiskBudgetValidationError(ValueError):
    """Validation failure for the exact registered portfolio-risk-budget v2 contract."""


def assert_risk_budget_schema_identity(schema_path: Path) -> None:
    digest = hashlib.sha256(schema_path.read_bytes()).hexdigest()
    if digest != RISK_BUDGET_SCHEMA_SHA256:
        raise RiskBudgetValidationError(
            "portfolio risk budget schema changed; requalification required"
        )


def _exact_object(
    value: Any,
    *,
    label: str,
    required: set[str],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RiskBudgetValidationError(f"{label} must be an object")
    keys = set(value)
    if keys != required:
        missing = sorted(required - keys)
        extra = sorted(keys - required)
        raise RiskBudgetValidationError(
            f"{label} keys mismatch; missing={missing}, extra={extra}"
        )
    return value


def validate_registered_risk_budget_document(doc: Any) -> dict[str, Any]:
    root_keys = {"schemaVersion", "kind", "standing", "owner", "limits"}
    root = _exact_object(doc, label="risk budget", required=root_keys)
    if root["schemaVersion"] != 2 or isinstance(root["schemaVersion"], bool):
        raise RiskBudgetValidationError("schemaVersion must equal 2")
    if root["kind"] != "ordivon.capital.risk.portfolio-risk-budget-registration":
        raise RiskBudgetValidationError("unexpected risk budget kind")
    standing = root["standing"]
    if standing not in {"UNSET", "ACTIVE"}:
        raise RiskBudgetValidationError("standing must be UNSET or ACTIVE")
    if root["owner"] != "OWNER_PRINCIPAL":
        raise RiskBudgetValidationError("owner must be OWNER_PRINCIPAL")

    limits = _exact_object(root["limits"], label="limits", required=_LIMIT_KEYS)
    for key in _LIMIT_KEYS:
        value = limits[key]
        allowed_type = (
            value is None
            or isinstance(value, str)
            or (isinstance(value, (int, float)) and not isinstance(value, bool))
        )
        if not allowed_type:
            raise RiskBudgetValidationError(f"limits.{key} has invalid type")
        if standing == "UNSET" and value is not None:
            raise RiskBudgetValidationError(f"limits.{key} must be null when UNSET")
        if standing == "ACTIVE" and value is None:
            raise RiskBudgetValidationError(f"limits.{key} must be non-null when ACTIVE")
    return root
