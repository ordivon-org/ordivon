from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ordivon_capital.risk.risk_budget_validation import (
    validate_registered_risk_budget_document,
)
from ordivon_capital.risk.risk_capacity_validation import validate_risk_capacity_document

CAPITAL_CONSTITUTION_SCHEMA_SHA256 = "f165afc8b9aac01731fd9e165f2bcb193c44559581228321b732962e081877d7"
DELEGATION_GRANT_SCHEMA_SHA256 = "c3979f18a3fb461af97abbe792ecb38b759c8d7955e3a3435c1152fe5f56bd21"
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")
_LEVELS = (
    "L0_OBSERVE",
    "L1_ANALYZE",
    "L2_RECOMMEND",
    "L3_PREPARE",
    "L4_EXECUTE_BOUNDED",
    "L5_CHANGE_CONSTITUTION",
)
_NON_L5_LEVELS = set(_LEVELS[:-1])
_EFFECT_STANDINGS = {
    "BLOCKED",
    "NON_LIVE_ONLY",
    "BOUNDED",
    "SEPARATE_APPROVAL_REQUIRED",
}


class OwnerAuthorityValidationError(ValueError):
    """Fail-closed validation error for owner Constitution/delegation documents."""


def _assert_schema_identity(path: Path, expected: str, label: str) -> None:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected:
        raise OwnerAuthorityValidationError(
            f"{label} schema changed; requalification required"
        )


def assert_capital_constitution_schema_identity(schema_path: Path) -> None:
    _assert_schema_identity(
        schema_path,
        CAPITAL_CONSTITUTION_SCHEMA_SHA256,
        "capital constitution",
    )


def assert_delegation_grant_schema_identity(schema_path: Path) -> None:
    _assert_schema_identity(
        schema_path,
        DELEGATION_GRANT_SCHEMA_SHA256,
        "delegation grant",
    )


def _exact_object(
    value: Any,
    *,
    label: str,
    required: set[str],
    optional: set[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise OwnerAuthorityValidationError(f"{label} must be an object")
    optional = optional or set()
    keys = set(value)
    missing = required - keys
    extra = keys - required - optional
    if missing or extra:
        raise OwnerAuthorityValidationError(
            f"{label} keys mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )
    return value


def _nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise OwnerAuthorityValidationError(f"{label} must be a non-empty string")
    return value


def _identifier(value: Any, label: str) -> str:
    text = _nonempty_string(value, label)
    if not _IDENTIFIER.fullmatch(text):
        raise OwnerAuthorityValidationError(f"{label} is not a valid identifier")
    return text


def _digest(value: Any, label: str) -> str:
    text = _nonempty_string(value, label)
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", text):
        raise OwnerAuthorityValidationError(f"{label} must be a sha256 digest")
    return text


def _datetime(value: Any, label: str) -> str:
    text = _nonempty_string(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OwnerAuthorityValidationError(f"{label} must be an RFC3339 date-time") from exc
    if parsed.tzinfo is None:
        raise OwnerAuthorityValidationError(f"{label} must include a timezone")
    return text


def _identifier_array(value: Any, label: str, *, min_items: int = 0) -> list[str]:
    if not isinstance(value, list) or len(value) < min_items:
        raise OwnerAuthorityValidationError(f"{label} must be an array")
    rows = [_identifier(item, f"{label}[]") for item in value]
    if len(rows) != len(set(rows)):
        raise OwnerAuthorityValidationError(f"{label} must be unique")
    return rows


def _string_array(value: Any, label: str, *, min_items: int = 0) -> list[str]:
    if not isinstance(value, list) or len(value) < min_items:
        raise OwnerAuthorityValidationError(f"{label} must be an array")
    rows = [_nonempty_string(item, f"{label}[]") for item in value]
    if len(rows) != len(set(rows)):
        raise OwnerAuthorityValidationError(f"{label} must be unique")
    return rows


def _validate_rule(value: Any, label: str) -> None:
    row = _exact_object(
        value,
        label=label,
        required={"ruleId", "scope", "statement"},
    )
    _identifier(row["ruleId"], f"{label}.ruleId")
    _nonempty_string(row["scope"], f"{label}.scope")
    _nonempty_string(row["statement"], f"{label}.statement")


def _validate_preference(value: Any, label: str) -> None:
    row = _exact_object(
        value,
        label=label,
        required={"preferenceId", "scope", "statement", "preferenceSource"},
    )
    _identifier(row["preferenceId"], f"{label}.preferenceId")
    _nonempty_string(row["scope"], f"{label}.scope")
    _nonempty_string(row["statement"], f"{label}.statement")
    if row["preferenceSource"] != "EXPLICIT_PRINCIPAL":
        raise OwnerAuthorityValidationError(
            f"{label}.preferenceSource must be EXPLICIT_PRINCIPAL"
        )


def validate_capital_constitution_document(doc: Any) -> dict[str, Any]:
    required = {
        "schemaVersion",
        "kind",
        "constitutionId",
        "principalAuthorityId",
        "purpose",
        "goals",
        "protectedResourceRules",
        "preferences",
        "prohibitions",
        "riskAppetite",
        "delegationPolicy",
        "effectClassPolicy",
        "reviewPolicy",
        "evidenceDigest",
    }
    root = _exact_object(
        doc,
        label="capital constitution",
        required=required,
        optional={"continuityPolicyRef"},
    )
    if root["schemaVersion"] != 1 or isinstance(root["schemaVersion"], bool):
        raise OwnerAuthorityValidationError("schemaVersion must equal 1")
    if root["kind"] != "ordivon.capital.constitution":
        raise OwnerAuthorityValidationError("unexpected capital constitution kind")
    _identifier(root["constitutionId"], "constitutionId")
    _identifier(root["principalAuthorityId"], "principalAuthorityId")
    _nonempty_string(root["purpose"], "purpose")
    _identifier_array(root["goals"], "goals")
    for index, row in enumerate(root["protectedResourceRules"]):
        _validate_rule(row, f"protectedResourceRules[{index}]")
    for index, row in enumerate(root["preferences"]):
        _validate_preference(row, f"preferences[{index}]")
    for index, row in enumerate(root["prohibitions"]):
        _validate_rule(row, f"prohibitions[{index}]")
    for index, row in enumerate(root["riskAppetite"]):
        _validate_preference(row, f"riskAppetite[{index}]")

    delegation = _exact_object(
        root["delegationPolicy"],
        label="delegationPolicy",
        required={"defaultMaximumLevel", "l5RequiresExplicitConstitutionalGrant"},
    )
    if delegation["defaultMaximumLevel"] not in _NON_L5_LEVELS:
        raise OwnerAuthorityValidationError("delegationPolicy.defaultMaximumLevel is invalid")
    if delegation["l5RequiresExplicitConstitutionalGrant"] is not True:
        raise OwnerAuthorityValidationError(
            "delegationPolicy must require explicit constitutional L5 grant"
        )

    policies = root["effectClassPolicy"]
    if not isinstance(policies, list):
        raise OwnerAuthorityValidationError("effectClassPolicy must be an array")
    for index, value in enumerate(policies):
        row = _exact_object(
            value,
            label=f"effectClassPolicy[{index}]",
            required={"effectClass", "standing", "maxDelegationLevel"},
        )
        _nonempty_string(row["effectClass"], f"effectClassPolicy[{index}].effectClass")
        if row["standing"] not in _EFFECT_STANDINGS:
            raise OwnerAuthorityValidationError(
                f"effectClassPolicy[{index}].standing is invalid"
            )
        if row["maxDelegationLevel"] not in _NON_L5_LEVELS:
            raise OwnerAuthorityValidationError(
                f"effectClassPolicy[{index}].maxDelegationLevel is invalid"
            )

    review = _exact_object(
        root["reviewPolicy"],
        label="reviewPolicy",
        required={"cadence", "eventDrivenReviewRequired"},
    )
    _nonempty_string(review["cadence"], "reviewPolicy.cadence")
    if not isinstance(review["eventDrivenReviewRequired"], bool):
        raise OwnerAuthorityValidationError(
            "reviewPolicy.eventDrivenReviewRequired must be boolean"
        )
    if "continuityPolicyRef" in root and root["continuityPolicyRef"] is not None:
        _nonempty_string(root["continuityPolicyRef"], "continuityPolicyRef")
    _digest(root["evidenceDigest"], "evidenceDigest")
    return root


def validate_delegation_grant_document(doc: Any) -> dict[str, Any]:
    required = {
        "schemaVersion",
        "kind",
        "grantId",
        "grantingAuthorityClass",
        "principalAuthorityId",
        "grantee",
        "level",
        "scopes",
        "effectClasses",
        "constitutionDigest",
        "validFrom",
        "revocable",
        "evidenceDigest",
    }
    root = _exact_object(
        doc,
        label="delegation grant",
        required=required,
        optional={"conditions", "validUntil", "constitutionalChangeAllowed"},
    )
    if root["schemaVersion"] != 1 or isinstance(root["schemaVersion"], bool):
        raise OwnerAuthorityValidationError("schemaVersion must equal 1")
    if root["kind"] != "ordivon.capital.delegation-grant":
        raise OwnerAuthorityValidationError("unexpected delegation grant kind")
    _identifier(root["grantId"], "grantId")
    if root["grantingAuthorityClass"] != "OWNER_PRINCIPAL":
        raise OwnerAuthorityValidationError("grantingAuthorityClass must be OWNER_PRINCIPAL")
    _identifier(root["principalAuthorityId"], "principalAuthorityId")
    grantee = _exact_object(
        root["grantee"],
        label="grantee",
        required={"granteeType", "granteeId"},
    )
    if grantee["granteeType"] not in {"OFFICE_ROLE", "AGENT_IDENTITY", "CAPABILITY_PROFILE"}:
        raise OwnerAuthorityValidationError("grantee.granteeType is invalid")
    _identifier(grantee["granteeId"], "grantee.granteeId")
    if root["level"] not in set(_LEVELS):
        raise OwnerAuthorityValidationError("delegation level is invalid")
    _string_array(root["scopes"], "scopes", min_items=1)
    _string_array(root["effectClasses"], "effectClasses")
    if "conditions" in root:
        if not isinstance(root["conditions"], list):
            raise OwnerAuthorityValidationError("conditions must be an array")
        for item in root["conditions"]:
            _nonempty_string(item, "conditions[]")
    _digest(root["constitutionDigest"], "constitutionDigest")
    _datetime(root["validFrom"], "validFrom")
    if "validUntil" in root and root["validUntil"] is not None:
        _datetime(root["validUntil"], "validUntil")
    if root["revocable"] is not True:
        raise OwnerAuthorityValidationError("delegation grants must be revocable")
    if "constitutionalChangeAllowed" in root and not isinstance(
        root["constitutionalChangeAllowed"], bool
    ):
        raise OwnerAuthorityValidationError("constitutionalChangeAllowed must be boolean")
    if root["level"] == "L5_CHANGE_CONSTITUTION" and root.get(
        "constitutionalChangeAllowed"
    ) is not True:
        raise OwnerAuthorityValidationError(
            "L5 delegation requires explicit constitutionalChangeAllowed=true"
        )
    _digest(root["evidenceDigest"], "evidenceDigest")
    return root


def project_owner_governance_envelope(
    *,
    constitution: dict[str, Any],
    delegation: dict[str, Any],
    risk_capacity: dict[str, Any],
    registered_risk_budget: dict[str, Any],
    required_level: str = "L2_RECOMMEND",
) -> dict[str, Any]:
    """Project owner/control standing without granting provider or effect authority.

    Risk capacity can tighten or block. It never fills an UNSET owner risk budget and
    never mints appetite, SIZE permission, credentials, provider permission or effects.
    """
    constitution = validate_capital_constitution_document(constitution)
    delegation = validate_delegation_grant_document(delegation)
    risk_capacity = validate_risk_capacity_document(risk_capacity)
    registered_risk_budget = validate_registered_risk_budget_document(
        registered_risk_budget
    )
    if required_level not in _LEVELS:
        raise OwnerAuthorityValidationError("required_level is invalid")
    if constitution["principalAuthorityId"] != delegation["principalAuthorityId"]:
        raise OwnerAuthorityValidationError(
            "constitution/delegation principal authority mismatch"
        )

    delegated = _LEVELS.index(delegation["level"]) >= _LEVELS.index(required_level)
    budget_active = registered_risk_budget["standing"] == "ACTIVE"
    capacity_standing = risk_capacity["standing"]

    if capacity_standing == "INSUFFICIENT":
        standing = "CAPACITY_BLOCKED"
    elif capacity_standing == "UNKNOWN":
        standing = "CAPACITY_REVIEW_REQUIRED"
    elif not delegated:
        standing = "DELEGATION_REVIEW_REQUIRED"
    elif not budget_active:
        standing = "RESEARCH_ONLY_RISK_BUDGET_UNSET"
    elif required_level == "L4_EXECUTE_BOUNDED":
        standing = "DOWNSTREAM_PROVIDER_AUTHORITY_REQUIRED"
    else:
        standing = "READY_FOR_BOUNDED_DOWNSTREAM_POLICY"

    sizing_permitted = (
        budget_active
        and delegated
        and capacity_standing in {"SUPPORTED", "CONSTRAINED"}
        and required_level != "L4_EXECUTE_BOUNDED"
    )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.owner-governance-envelope",
        "standing": standing,
        "principalAuthorityId": constitution["principalAuthorityId"],
        "requiredDelegationLevel": required_level,
        "delegatedLevel": delegation["level"],
        "delegationSatisfied": delegated,
        "riskCapacityStanding": capacity_standing,
        "riskCapacityRole": "SAFETY_ENVELOPE_ONLY",
        "riskBudgetStanding": registered_risk_budget["standing"],
        "ownerRiskAppetiteInferred": False,
        "riskBudgetSynthesized": False,
        "sizingEligibleForDownstreamPolicy": sizing_permitted,
        "providerPermissionGranted": False,
        "credentialAuthorityGranted": False,
        "externalEffectAuthorityGranted": False,
        "externalEffectCommitted": False,
    }
