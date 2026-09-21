from __future__ import annotations

import copy
import importlib.util
import json
import random
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]


def _load_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_risk_validation = _load_module(
    "ordivon_r18_risk_validation",
    "src/ordivon_capital/risk/risk_budget_validation.py",
)
_inventory_validation = _load_module(
    "ordivon_r18_inventory_validation",
    "src/ordivon_capital/research/quantitative_inventory_validation.py",
)
RiskBudgetValidationError = _risk_validation.RiskBudgetValidationError
validate_registered_risk_budget_document = (
    _risk_validation.validate_registered_risk_budget_document
)
QuantitativeInventoryValidationError = (
    _inventory_validation.QuantitativeInventoryValidationError
)
validate_quantitative_component_inventory_document = (
    _inventory_validation.validate_quantitative_component_inventory_document
)
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

CLASSIFICATIONS = {
    "QUANTITATIVE_MODEL",
    "ANALYTICAL_HEURISTIC",
    "NON_MODEL_CALCULATION",
    "CONTROL",
    "ADAPTER",
    "RECONCILIATION",
}
MODEL_STANDINGS = {"MODEL", "NON_MODEL", "CLASSIFICATION_REVIEW"}
STATUSES = {"ACTIVE", "RESEARCH_ONLY", "VALIDATION_REQUIRED", "RETIRED"}
MATERIALITIES = {"LOW", "MEDIUM", "HIGH", "NOT_APPLICABLE"}
VALIDATION_STANDINGS = {
    "NOT_APPLICABLE",
    "DEVELOPMENT_TESTED",
    "VALIDATION_REQUIRED",
    "RETIRED_UNVALIDATED",
}
MONITORING_STANDINGS = {"NOT_APPLICABLE", "REQUIRED", "ACTIVE", "RETIRED"}


class LocalValidationError(ValueError):
    pass


def _object(value: Any, name: str, *, keys: set[str], required: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LocalValidationError(f"{name} must be object")
    extra = set(value) - keys
    missing = required - set(value)
    if extra:
        raise LocalValidationError(f"{name} extra properties: {sorted(extra)}")
    if missing:
        raise LocalValidationError(f"{name} missing required: {sorted(missing)}")
    return value


def _string(value: Any, name: str, *, min_length: int = 0) -> str:
    if not isinstance(value, str):
        raise LocalValidationError(f"{name} must be string")
    if len(value) < min_length:
        raise LocalValidationError(f"{name} too short")
    return value


def _array(value: Any, name: str, *, min_items: int = 0) -> list[Any]:
    if not isinstance(value, list):
        raise LocalValidationError(f"{name} must be array")
    if len(value) < min_items:
        raise LocalValidationError(f"{name} too short")
    return value


def _const(value: Any, expected: Any, name: str) -> None:
    if isinstance(value, bool) != isinstance(expected, bool) and (
        isinstance(value, bool) or isinstance(expected, bool)
    ):
        raise LocalValidationError(f"{name} const mismatch")
    if value != expected:
        raise LocalValidationError(f"{name} const mismatch")


def validate_risk_budget(doc: Any) -> None:
    root = _object(
        doc,
        "root",
        keys={"schemaVersion", "kind", "standing", "owner", "limits"},
        required={"schemaVersion", "kind", "standing", "owner", "limits"},
    )
    _const(root["schemaVersion"], 2, "schemaVersion")
    _const(
        root["kind"],
        "ordivon.capital.risk.portfolio-risk-budget-registration",
        "kind",
    )
    standing = root["standing"]
    if standing not in {"UNSET", "ACTIVE"}:
        raise LocalValidationError("standing enum mismatch")
    _const(root["owner"], "OWNER_PRINCIPAL", "owner")

    limit_keys = {
        "maxGrossToEquity",
        "maxLargestPositionGrossShare",
        "minAvailableEquityRatio",
        "shockMagnitudePct",
        "maxEquityLossPctAtShock",
    }
    limits = _object(
        root["limits"],
        "limits",
        keys=limit_keys,
        required=limit_keys,
    )
    for key in limit_keys:
        value = limits[key]
        type_ok = (
            value is None
            or isinstance(value, str)
            or (isinstance(value, (int, float)) and not isinstance(value, bool))
        )
        if not type_ok:
            raise LocalValidationError(f"limits.{key} type mismatch")
        if standing == "UNSET" and value is not None:
            raise LocalValidationError(f"limits.{key} must be null when UNSET")
        if standing == "ACTIVE" and value is None:
            raise LocalValidationError(f"limits.{key} must be non-null when ACTIVE")


def _string_array(
    value: Any,
    name: str,
    *,
    min_items: int = 0,
    item_min_length: int = 0,
) -> None:
    rows = _array(value, name, min_items=min_items)
    for i, item in enumerate(rows):
        _string(item, f"{name}[{i}]", min_length=item_min_length)


def validate_quant_inventory(doc: Any) -> None:
    root = _object(
        doc,
        "root",
        keys={"schemaVersion", "framework", "classificationBoundary", "components"},
        required={"schemaVersion", "framework", "classificationBoundary", "components"},
    )
    _const(root["schemaVersion"], 1, "schemaVersion")

    framework = _object(
        root["framework"],
        "framework",
        keys={"name", "issued", "standing"},
        required={"name", "issued", "standing"},
    )
    _const(
        framework["name"],
        "Federal Reserve SR 26-2 Revised Guidance on Model Risk Management",
        "framework.name",
    )
    _const(framework["issued"], "2026-04-17", "framework.issued")
    _const(
        framework["standing"],
        "REFERENCE_GOVERNANCE_FRAMEWORK",
        "framework.standing",
    )
    _string(root["classificationBoundary"], "classificationBoundary", min_length=20)

    components = _array(root["components"], "components", min_items=1)
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
    for i, raw in enumerate(components):
        prefix = f"components[{i}]"
        row = _object(raw, prefix, keys=allowed, required=required)
        ident = _string(row["id"], f"{prefix}.id")
        if ID_RE.fullmatch(ident) is None:
            raise LocalValidationError(f"{prefix}.id pattern mismatch")
        _string(row["implementation"], f"{prefix}.implementation", min_length=3)
        if row["classification"] not in CLASSIFICATIONS:
            raise LocalValidationError(f"{prefix}.classification enum mismatch")
        if row["sr26ModelStanding"] not in MODEL_STANDINGS:
            raise LocalValidationError(f"{prefix}.sr26ModelStanding enum mismatch")
        if row["status"] not in STATUSES:
            raise LocalValidationError(f"{prefix}.status enum mismatch")
        _string(row["purpose"], f"{prefix}.purpose", min_length=10)
        if row["materiality"] not in MATERIALITIES:
            raise LocalValidationError(f"{prefix}.materiality enum mismatch")

        _string_array(row["assumptions"], f"{prefix}.assumptions", item_min_length=3)
        _string_array(
            row["limitations"],
            f"{prefix}.limitations",
            min_items=1,
            item_min_length=3,
        )

        validation = _object(
            row["validation"],
            f"{prefix}.validation",
            keys={"standing", "evidenceRefs"},
            required={"standing", "evidenceRefs"},
        )
        if validation["standing"] not in VALIDATION_STANDINGS:
            raise LocalValidationError(f"{prefix}.validation.standing enum mismatch")
        _string_array(validation["evidenceRefs"], f"{prefix}.validation.evidenceRefs")

        monitoring = _object(
            row["monitoring"],
            f"{prefix}.monitoring",
            keys={"standing", "requirements"},
            required={"standing", "requirements"},
        )
        if monitoring["standing"] not in MONITORING_STANDINGS:
            raise LocalValidationError(f"{prefix}.monitoring.standing enum mismatch")
        _string_array(monitoring["requirements"], f"{prefix}.monitoring.requirements")

        _string_array(row["permittedUses"], f"{prefix}.permittedUses", min_items=1)
        _string_array(row["prohibitedUses"], f"{prefix}.prohibitedUses", min_items=1)
        if "retirementReason" in row:
            _string(row["retirementReason"], f"{prefix}.retirementReason")
        if row["status"] == "RETIRED" and "retirementReason" not in row:
            raise LocalValidationError(f"{prefix}.retirementReason required")


def _is_local_valid(kind: str, doc: Any) -> bool:
    try:
        if kind == "risk":
            validate_registered_risk_budget_document(doc)
        else:
            validate_quantitative_component_inventory_document(doc)
    except (RiskBudgetValidationError, QuantitativeInventoryValidationError):
        return False
    return True


def _is_external_valid(schema: dict[str, Any], doc: Any) -> bool:
    return Draft202012Validator(schema).is_valid(doc)


def _mutate_risk(base: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    doc = copy.deepcopy(base)
    choices = [
        "valid_active",
        "drop_root",
        "root_extra",
        "schema",
        "kind",
        "standing",
        "owner",
        "limits_not_object",
        "drop_limit",
        "limit_extra",
        "limit_bad_type",
        "unset_nonnull",
        "active_null",
    ]
    choice = rng.choice(choices)
    keys = list(doc["limits"])
    if choice == "valid_active":
        doc["standing"] = "ACTIVE"
        for key in keys:
            doc["limits"][key] = rng.choice([1, 1.25, "0.5", "", -3])
    elif choice == "drop_root":
        doc.pop(rng.choice(list(doc)))
    elif choice == "root_extra":
        doc["extra"] = 1
    elif choice == "schema":
        doc["schemaVersion"] = rng.choice([1, "2", True, None, 3])
    elif choice == "kind":
        doc["kind"] = rng.choice(["x", 1, None])
    elif choice == "standing":
        doc["standing"] = rng.choice(["", "PAUSED", 1, None])
    elif choice == "owner":
        doc["owner"] = rng.choice(["OTHER", 1, None])
    elif choice == "limits_not_object":
        doc["limits"] = rng.choice([[], "x", 1, None])
    elif choice == "drop_limit":
        doc["limits"].pop(rng.choice(keys))
    elif choice == "limit_extra":
        doc["limits"]["extra"] = 1
    elif choice == "limit_bad_type":
        doc["limits"][rng.choice(keys)] = rng.choice([[], {}, True])
    elif choice == "unset_nonnull":
        doc["standing"] = "UNSET"
        doc["limits"][rng.choice(keys)] = rng.choice([0, "0", -1])
    elif choice == "active_null":
        doc["standing"] = "ACTIVE"
        for key in keys:
            doc["limits"][key] = 1
        doc["limits"][rng.choice(keys)] = None
    return doc


def _mutate_inventory(base: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    doc = copy.deepcopy(base)
    row = rng.choice(doc["components"])
    choices = [
        "valid_copy",
        "drop_root",
        "root_extra",
        "schema",
        "framework_drop",
        "framework_extra",
        "framework_const",
        "boundary_short",
        "components_empty",
        "components_not_array",
        "component_drop",
        "component_extra",
        "id_pattern",
        "implementation_short",
        "classification",
        "model_standing",
        "status",
        "purpose_short",
        "materiality",
        "assumptions_bad",
        "limitations_empty",
        "limitations_short",
        "validation_drop",
        "validation_extra",
        "validation_standing",
        "evidence_bad",
        "monitoring_drop",
        "monitoring_extra",
        "monitoring_standing",
        "requirements_bad",
        "permitted_empty",
        "prohibited_empty",
        "retired_missing_reason",
        "valid_retired",
    ]
    choice = rng.choice(choices)
    if choice == "valid_copy":
        pass
    elif choice == "drop_root":
        doc.pop(rng.choice(list(doc)))
    elif choice == "root_extra":
        doc["extra"] = True
    elif choice == "schema":
        doc["schemaVersion"] = rng.choice([0, "1", True, None])
    elif choice == "framework_drop":
        doc["framework"].pop(rng.choice(list(doc["framework"])))
    elif choice == "framework_extra":
        doc["framework"]["extra"] = 1
    elif choice == "framework_const":
        doc["framework"][rng.choice(["name", "issued", "standing"])] = "wrong"
    elif choice == "boundary_short":
        doc["classificationBoundary"] = rng.choice(["", "short", 1, None])
    elif choice == "components_empty":
        doc["components"] = []
    elif choice == "components_not_array":
        doc["components"] = rng.choice([{}, "x", None])
    elif choice == "component_drop":
        row.pop(rng.choice([k for k in row if k != "retirementReason"]))
    elif choice == "component_extra":
        row["extra"] = 1
    elif choice == "id_pattern":
        row["id"] = rng.choice(["Bad ID", "-bad", "", 1])
    elif choice == "implementation_short":
        row["implementation"] = rng.choice(["", "x", "xy", 1])
    elif choice == "classification":
        row["classification"] = "OTHER"
    elif choice == "model_standing":
        row["sr26ModelStanding"] = "OTHER"
    elif choice == "status":
        row["status"] = "OTHER"
    elif choice == "purpose_short":
        row["purpose"] = rng.choice(["", "short", 1])
    elif choice == "materiality":
        row["materiality"] = "OTHER"
    elif choice == "assumptions_bad":
        row["assumptions"] = rng.choice([["x"], "bad", [1]])
    elif choice == "limitations_empty":
        row["limitations"] = []
    elif choice == "limitations_short":
        row["limitations"] = ["x"]
    elif choice == "validation_drop":
        row["validation"].pop(rng.choice(list(row["validation"])))
    elif choice == "validation_extra":
        row["validation"]["extra"] = 1
    elif choice == "validation_standing":
        row["validation"]["standing"] = "OTHER"
    elif choice == "evidence_bad":
        row["validation"]["evidenceRefs"] = rng.choice(["x", [1]])
    elif choice == "monitoring_drop":
        row["monitoring"].pop(rng.choice(list(row["monitoring"])))
    elif choice == "monitoring_extra":
        row["monitoring"]["extra"] = 1
    elif choice == "monitoring_standing":
        row["monitoring"]["standing"] = "OTHER"
    elif choice == "requirements_bad":
        row["monitoring"]["requirements"] = rng.choice(["x", [1]])
    elif choice == "permitted_empty":
        row["permittedUses"] = []
    elif choice == "prohibited_empty":
        row["prohibitedUses"] = []
    elif choice == "retired_missing_reason":
        row["status"] = "RETIRED"
        row.pop("retirementReason", None)
    elif choice == "valid_retired":
        row["status"] = "RETIRED"
        row["retirementReason"] = "retired for bounded differential qualification"
    return doc


def main() -> None:
    risk_schema = json.loads((ROOT / "contracts/portfolio-risk-budget-v2.schema.json").read_text())
    inv_schema = json.loads((ROOT / "schema/quantitative_component_inventory.schema.json").read_text())
    risk = json.loads((ROOT / "config/portfolio_risk_budget.json").read_text())
    inventory = json.loads((ROOT / "config/quantitative_component_inventory.json").read_text())
    assert _is_external_valid(risk_schema, risk) and _is_local_valid("risk", risk)
    assert _is_external_valid(inv_schema, inventory) and _is_local_valid("inventory", inventory)

    rng = random.Random(20260921)
    mismatch: list[dict[str, Any]] = []
    counts = {"risk": 0, "inventory": 0}
    for _ in range(2000):
        doc = _mutate_risk(risk, rng)
        external = _is_external_valid(risk_schema, doc)
        local = _is_local_valid("risk", doc)
        counts["risk"] += 1
        if external != local:
            mismatch.append({"kind": "risk", "external": external, "local": local, "doc": doc})
            break
    if not mismatch:
        for _ in range(4000):
            doc = _mutate_inventory(inventory, rng)
            external = _is_external_valid(inv_schema, doc)
            local = _is_local_valid("inventory", doc)
            counts["inventory"] += 1
            if external != local:
                mismatch.append(
                    {"kind": "inventory", "external": external, "local": local, "doc": doc}
                )
                break

    source_lines = len(Path(__file__).read_text().splitlines())
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.jsonschema-local-baseline-r18",
        "standing": "PASS_ZERO_MISMATCH" if not mismatch else "FAIL_DIFFERENTIAL_MISMATCH",
        "jsonschemaVersion": "4.26.0",
        "cases": counts,
        "totalCases": sum(counts.values()),
        "mismatches": len(mismatch),
        "candidateSourceLinesIncludingHarness": source_lines,
        "activeSchemas": 2,
        "externalFinancialWriteAttempted": False,
    }
    if mismatch:
        result["firstMismatch"] = mismatch[0]
    print(json.dumps(result, sort_keys=True))
    if mismatch:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
