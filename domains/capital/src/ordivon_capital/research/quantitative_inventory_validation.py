from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

QUANTITATIVE_INVENTORY_SCHEMA_SHA256 = "656d1fa9eb6154f98934a52be5f8206dcbc1b6cd8275f7135dd243d22004b1e0"
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_CLASSIFICATIONS = {
    "QUANTITATIVE_MODEL",
    "ANALYTICAL_HEURISTIC",
    "NON_MODEL_CALCULATION",
    "CONTROL",
    "ADAPTER",
    "RECONCILIATION",
}
_MODEL_STANDINGS = {"MODEL", "NON_MODEL", "CLASSIFICATION_REVIEW"}
_STATUSES = {"ACTIVE", "RESEARCH_ONLY", "VALIDATION_REQUIRED", "RETIRED"}
_MATERIALITIES = {"LOW", "MEDIUM", "HIGH", "NOT_APPLICABLE"}
_VALIDATION_STANDINGS = {
    "NOT_APPLICABLE",
    "DEVELOPMENT_TESTED",
    "VALIDATION_REQUIRED",
    "RETIRED_UNVALIDATED",
}
_MONITORING_STANDINGS = {"NOT_APPLICABLE", "REQUIRED", "ACTIVE", "RETIRED"}


class QuantitativeInventoryValidationError(ValueError):
    """Validation failure for the exact quantitative-component inventory contract."""


def assert_quantitative_inventory_schema_identity(schema_path: Path) -> None:
    digest = hashlib.sha256(schema_path.read_bytes()).hexdigest()
    if digest != QUANTITATIVE_INVENTORY_SCHEMA_SHA256:
        raise QuantitativeInventoryValidationError(
            "quantitative inventory schema changed; requalification required"
        )


def _object(
    value: Any,
    *,
    label: str,
    allowed: set[str],
    required: set[str],
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise QuantitativeInventoryValidationError(f"{label} must be an object")
    keys = set(value)
    missing = required - keys
    extra = keys - allowed
    if missing or extra:
        raise QuantitativeInventoryValidationError(
            f"{label} keys mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )
    return value


def _string(value: Any, *, label: str, min_length: int = 0) -> str:
    if not isinstance(value, str):
        raise QuantitativeInventoryValidationError(f"{label} must be a string")
    if len(value) < min_length:
        raise QuantitativeInventoryValidationError(f"{label} is too short")
    return value


def _string_array(
    value: Any,
    *,
    label: str,
    min_items: int = 0,
    item_min_length: int = 0,
) -> list[str]:
    if not isinstance(value, list) or len(value) < min_items:
        raise QuantitativeInventoryValidationError(f"{label} must be a valid array")
    for index, item in enumerate(value):
        _string(item, label=f"{label}[{index}]", min_length=item_min_length)
    return value


def validate_quantitative_component_inventory_document(doc: Any) -> dict[str, Any]:
    root_allowed = {"schemaVersion", "framework", "classificationBoundary", "components"}
    root = _object(doc, label="inventory", allowed=root_allowed, required=root_allowed)
    if root["schemaVersion"] != 1 or isinstance(root["schemaVersion"], bool):
        raise QuantitativeInventoryValidationError("schemaVersion must equal 1")

    framework_keys = {"name", "issued", "standing"}
    framework = _object(
        root["framework"],
        label="framework",
        allowed=framework_keys,
        required=framework_keys,
    )
    constants = {
        "name": "Federal Reserve SR 26-2 Revised Guidance on Model Risk Management",
        "issued": "2026-04-17",
        "standing": "REFERENCE_GOVERNANCE_FRAMEWORK",
    }
    for key, expected in constants.items():
        if framework[key] != expected:
            raise QuantitativeInventoryValidationError(f"framework.{key} mismatch")

    _string(root["classificationBoundary"], label="classificationBoundary", min_length=20)
    components = root["components"]
    if not isinstance(components, list) or not components:
        raise QuantitativeInventoryValidationError("components must be a non-empty array")

    allowed = {
        "id",
        "implementation",
        "classification",
        "sr26ModelStanding",
        "status",
        "purpose",
        "materiality",
        "assumptions",
        "limitations",
        "validation",
        "monitoring",
        "permittedUses",
        "prohibitedUses",
        "retirementReason",
    }
    required = allowed - {"retirementReason"}
    for index, raw in enumerate(components):
        label = f"components[{index}]"
        row = _object(raw, label=label, allowed=allowed, required=required)
        identifier = _string(row["id"], label=f"{label}.id")
        if _ID_RE.fullmatch(identifier) is None:
            raise QuantitativeInventoryValidationError(f"{label}.id pattern mismatch")
        _string(row["implementation"], label=f"{label}.implementation", min_length=3)
        if row["classification"] not in _CLASSIFICATIONS:
            raise QuantitativeInventoryValidationError(f"{label}.classification mismatch")
        if row["sr26ModelStanding"] not in _MODEL_STANDINGS:
            raise QuantitativeInventoryValidationError(f"{label}.sr26ModelStanding mismatch")
        if row["status"] not in _STATUSES:
            raise QuantitativeInventoryValidationError(f"{label}.status mismatch")
        _string(row["purpose"], label=f"{label}.purpose", min_length=10)
        if row["materiality"] not in _MATERIALITIES:
            raise QuantitativeInventoryValidationError(f"{label}.materiality mismatch")
        _string_array(
            row["assumptions"],
            label=f"{label}.assumptions",
            item_min_length=3,
        )
        _string_array(
            row["limitations"],
            label=f"{label}.limitations",
            min_items=1,
            item_min_length=3,
        )

        validation_keys = {"standing", "evidenceRefs"}
        validation = _object(
            row["validation"],
            label=f"{label}.validation",
            allowed=validation_keys,
            required=validation_keys,
        )
        if validation["standing"] not in _VALIDATION_STANDINGS:
            raise QuantitativeInventoryValidationError(
                f"{label}.validation.standing mismatch"
            )
        _string_array(
            validation["evidenceRefs"],
            label=f"{label}.validation.evidenceRefs",
        )

        monitoring_keys = {"standing", "requirements"}
        monitoring = _object(
            row["monitoring"],
            label=f"{label}.monitoring",
            allowed=monitoring_keys,
            required=monitoring_keys,
        )
        if monitoring["standing"] not in _MONITORING_STANDINGS:
            raise QuantitativeInventoryValidationError(
                f"{label}.monitoring.standing mismatch"
            )
        _string_array(
            monitoring["requirements"],
            label=f"{label}.monitoring.requirements",
        )

        _string_array(
            row["permittedUses"],
            label=f"{label}.permittedUses",
            min_items=1,
        )
        _string_array(
            row["prohibitedUses"],
            label=f"{label}.prohibitedUses",
            min_items=1,
        )
        if "retirementReason" in row:
            _string(row["retirementReason"], label=f"{label}.retirementReason")
        if row["status"] == "RETIRED" and "retirementReason" not in row:
            raise QuantitativeInventoryValidationError(
                f"{label}.retirementReason required when RETIRED"
            )
    return root
