from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]


class CompositionContractError(ValueError):
    """Fail-closed Capital LEGO composition error."""


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text())
    if not isinstance(value, dict):
        raise CompositionContractError(f"expected JSON object: {relative}")
    return value


def _normalize_use(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").replace("-", " ").split())


def _registry_by_id() -> dict[str, dict[str, Any]]:
    registry = _load("config/capital_lego_registry.json")
    return {row["legoId"]: row for row in registry["entries"]}


def _role_evidence(roles: Iterable[str]) -> list[str]:
    catalog = _load("contracts/capital-evidence-obligation-v1.json")
    by_role = catalog["byFunctionalRole"]
    result: list[str] = []
    for role in roles:
        for item in by_role[role]:
            if item not in result:
                result.append(item)
    return result


def _effect_evidence(effect_class: str) -> list[str]:
    catalog = _load("contracts/capital-evidence-obligation-v1.json")
    return list(catalog["byEffectClass"][effect_class])


def _effect_contract(effect_class: str) -> dict[str, Any]:
    catalog = _load("contracts/capital-effect-class-v1.json")
    return dict(catalog["classes"][effect_class])


def compile_composition(
    *,
    lego_ids: list[str],
    available_authorities: set[str] | frozenset[str],
    requested_use: str,
    allow_challengers: bool = False,
) -> dict[str, Any]:
    """Validate and project one ordered Capital LEGO composition.

    This is a composition admission only. It never executes a node, proves evidence
    obligations satisfied, or grants authority.
    """
    if not lego_ids:
        raise CompositionContractError("composition requires at least one LEGO")
    if len(set(lego_ids)) != len(lego_ids):
        raise CompositionContractError("R1 composition rejects duplicate LEGO identities")

    rows = _registry_by_id()
    authority_contract = _load("contracts/capital-authority-requirement-v1.json")
    known_authorities = set(authority_contract["classes"])
    unknown = set(available_authorities) - known_authorities
    if unknown:
        raise CompositionContractError(f"unknown authority classes: {sorted(unknown)}")

    normalized_use = _normalize_use(requested_use)
    steps: list[dict[str, Any]] = []
    all_roles: list[set[str]] = []
    effect_positions: list[tuple[int, str]] = []
    obligations: list[str] = []

    for position, lego_id in enumerate(lego_ids):
        row = rows.get(lego_id)
        if row is None:
            raise CompositionContractError(f"unregistered LEGO: {lego_id}")
        status = row["status"]
        if status == "RETIRED":
            raise CompositionContractError(f"{lego_id}: retired LEGO cannot compose")
        if status == "CHALLENGER" and not allow_challengers:
            raise CompositionContractError(
                f"{lego_id}: challenger cannot enter canonical composition"
            )
        if status == "BLOCKED_BY_AUTHORITY":
            raise CompositionContractError(
                f"{lego_id}: current source is blocked by independent authority/currentness"
            )

        authority = row["authorityRequirement"]
        if authority != "NONE" and authority not in available_authorities:
            raise CompositionContractError(
                f"{lego_id}: required authority {authority} not supplied"
            )
        authority_meta = authority_contract["classes"][authority]
        if authority_meta["currentAdmission"] is False and status != "CHALLENGER":
            raise CompositionContractError(
                f"{lego_id}: authority class {authority} is not currently admitted"
            )

        for prohibited in row["prohibitedUses"]:
            if normalized_use and _normalize_use(prohibited) == normalized_use:
                raise CompositionContractError(
                    f"{lego_id}: requested use is explicitly prohibited: {requested_use}"
                )

        roles = set(row["functionalRoles"])
        all_roles.append(roles)
        effect_class = row["effectClass"]
        if effect_class not in {"NONE", "LOCAL_STATE"}:
            effect_positions.append((position, effect_class))

        step_obligations = []
        for item in [*row["evidenceObligations"], *_role_evidence(row["functionalRoles"]), *_effect_evidence(effect_class)]:
            if item not in step_obligations:
                step_obligations.append(item)
            if item not in obligations:
                obligations.append(item)

        steps.append({
            "position": position,
            "legoId": lego_id,
            "assumptions": {
                "authorityRequirement": authority,
                "currentnessRequirement": row["currentnessRequirement"],
                "evidenceObligations": step_obligations,
            },
            "guarantees": {
                "ownerDomain": row["ownerDomain"],
                "functionalRoles": row["functionalRoles"],
                "effectClass": effect_class,
                "outputContracts": row["outputContracts"],
                "permittedUses": row["permittedUses"],
                "prohibitedUses": row["prohibitedUses"],
            },
        })

    production = _load("contracts/production-authorization.json")
    for effect_position, effect_class in effect_positions:
        meta = _effect_contract(effect_class)
        if effect_class == "PRODUCTION_FINANCIAL_WRITE":
            if production["state"] != "ADMITTED" or production["externalFinancialWriteAllowed"] is not True:
                raise CompositionContractError("production financial write is not authorized")
        if meta["requiresReservation"]:
            if not any("Reserve" in roles for roles in all_roles[:effect_position]):
                raise CompositionContractError(
                    f"{effect_class}: Reserve LEGO must precede provider effect"
                )
        if meta["requiresReconciliation"]:
            if not any("Reconcile" in roles for roles in all_roles[effect_position + 1 :]):
                raise CompositionContractError(
                    f"{effect_class}: a distinct downstream Reconcile LEGO is required"
                )
        if meta["requiresAccountingResolution"]:
            if not any("Account" in roles for roles in all_roles[effect_position + 1 :]):
                raise CompositionContractError(
                    f"{effect_class}: downstream Account LEGO is required"
                )

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.composition-admission",
        "standing": "ADMITTED_COMPOSITION_ONLY",
        "requestedUse": requested_use,
        "availableAuthorities": sorted(available_authorities),
        "steps": steps,
        "unresolvedEvidenceObligations": obligations,
        "effectClasses": [effect for _, effect in effect_positions],
        "semanticCompletionEvaluated": False,
        "authorityGranted": False,
        "executionPerformed": False,
    }
