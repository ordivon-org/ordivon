#!/usr/bin/env python3
"""Pure provider-boundary diagnosis and admission policy for Agent Automation.

This module never accesses provider, browser, network, profile state, or external effects.
It projects one explicit provider action from an observation so diagnosis and effect
executors can share one policy authority.
"""

from __future__ import annotations

from typing import Any

POLICY_VERSION = "provider-boundary-r2"
NEUTRAL_ATTRIBUTION_REFERENCE = "browser-security-r9"

CARRIER_FAILOVER_STANDINGS = frozenset(
    {
        "SUBSTRATE_UNAVAILABLE",
        "CARRIER_BUSY",
        "PROVIDER_UNAVAILABLE",
        "CONNECT_FAILED",
    }
)

PROVIDER_NOT_ADMISSIBLE_STANDINGS = frozenset(
    {
        "CHALLENGE_GATED",
        "AUTH_REQUIRED",
        "PROVIDER_RATE_LIMITED",
    }
)

PROVIDER_UI_UNRESOLVED_STANDINGS = frozenset(
    {
        "CONTEXT_UNAVAILABLE",
        "COMPOSER_UNAVAILABLE",
    }
)

PROVIDER_ACTION_CONTINUE = "CONTINUE_MATERIALIZATION"
PROVIDER_ACTION_FAILOVER = "TRY_NEXT_CARRIER"
PROVIDER_ACTION_HUMAN_CONTROL_TRANSFER = "HUMAN_CONTROL_TRANSFER"
PROVIDER_ACTION_HOLD = "PRE_EFFECT_HOLD"
PROVIDER_ACTION_WAIT = "WAIT_FOR_PROVIDER_CONDITION_CHANGE"

_INFRASTRUCTURE_REPAIRS = (
    "rotate-carrier",
    "restart-carrier",
    "clear-profile",
    "mutate-launcher-flags",
    "mutate-network-authority",
)


def provider_action_for_standing(standing: str) -> str:
    """Return the single admission action for one provider standing.

    Unknown or UI-unresolved standings fail closed before provider effect.
    """
    if standing == "READY":
        return PROVIDER_ACTION_CONTINUE
    if standing in CARRIER_FAILOVER_STANDINGS:
        return PROVIDER_ACTION_FAILOVER
    if standing == "AUTH_REQUIRED":
        return PROVIDER_ACTION_HUMAN_CONTROL_TRANSFER
    if standing == "PROVIDER_RATE_LIMITED":
        return PROVIDER_ACTION_WAIT
    return PROVIDER_ACTION_HOLD


def _substrate_standing(observation: dict[str, Any]) -> str:
    substrate = observation.get("substrateHealth")
    if not isinstance(substrate, dict):
        return "UNKNOWN"
    healthy = substrate.get("healthy")
    if healthy is True:
        return "HEALTHY"
    if healthy is False:
        return "UNHEALTHY"
    return "UNKNOWN"


def _policy_metadata() -> dict[str, Any]:
    return {
        "policyVersion": POLICY_VERSION,
        "neutralAttributionReference": {
            "reference": NEUTRAL_ATTRIBUTION_REFERENCE,
            "standing": "REFERENCE_ONLY_NOT_LIVE_ASSERTION",
        },
        "providerRootCauseEstablished": False,
    }


def provider_boundary_policy() -> dict[str, Any]:
    """Static policy projection suitable for doctor/release currentness output."""
    action_table = {
        standing: provider_action_for_standing(standing)
        for standing in sorted(
            {
                "READY",
                *CARRIER_FAILOVER_STANDINGS,
                *PROVIDER_NOT_ADMISSIBLE_STANDINGS,
                *PROVIDER_UI_UNRESOLVED_STANDINGS,
            }
        )
    }
    return {
        "schemaVersion": 1,
        "kind": "ordivon.provider-boundary-policy",
        **_policy_metadata(),
        "automaticInfrastructureMutationFromProviderBoundary": False,
        "carrierFailoverStandings": sorted(CARRIER_FAILOVER_STANDINGS),
        "providerNotAdmissibleStandings": sorted(PROVIDER_NOT_ADMISSIBLE_STANDINGS),
        "providerUiUnresolvedStandings": sorted(PROVIDER_UI_UNRESOLVED_STANDINGS),
        "providerActions": action_table,
        "forbiddenAutomaticInfrastructureRepairs": list(_INFRASTRUCTURE_REPAIRS),
    }


def diagnose_provider_preflight(observation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(observation, dict):
        raise ValueError("provider preflight observation must be an object")
    standing = observation.get("standing")
    if not isinstance(standing, str) or not standing:
        raise ValueError("provider preflight standing is required")

    substrate = _substrate_standing(observation)
    provider_action = provider_action_for_standing(standing)
    carrier_routing = "PRESERVE_SELECTED_CARRIER"
    provider_admission = "UNRESOLVED"
    human_verification_eligible = standing == "AUTH_REQUIRED"
    reentry = "EXPLICIT_AFTER_CONDITION_CHANGE"
    allowed = ["record-telemetry", "preserve-selected-carrier"]
    state = "PREFLIGHT_UNRESOLVED"

    if provider_action == PROVIDER_ACTION_FAILOVER:
        state = "CARRIER_PRE_EFFECT_UNAVAILABLE"
        carrier_routing = "FAILOVER_ALLOWED"
        provider_admission = "NOT_OBSERVED"
        human_verification_eligible = False
        reentry = "TRY_NEXT_CARRIER"
        allowed = ["record-telemetry", "try-next-carrier"]
    elif provider_action == PROVIDER_ACTION_CONTINUE:
        state = "PROVIDER_ADMISSIBLE"
        provider_admission = "ADMISSIBLE"
        human_verification_eligible = False
        reentry = "CONTINUE_MATERIALIZATION"
        allowed = ["record-telemetry", "preserve-selected-carrier", "continue-materialization"]
    elif standing in PROVIDER_NOT_ADMISSIBLE_STANDINGS:
        state = (
            "SUBSTRATE_HEALTHY_PROVIDER_NOT_ADMISSIBLE"
            if substrate == "HEALTHY"
            else f"PROVIDER_NOT_ADMISSIBLE_SUBSTRATE_{substrate}"
        )
        provider_admission = "NOT_ADMISSIBLE"
        if provider_action == PROVIDER_ACTION_HUMAN_CONTROL_TRANSFER:
            reentry = "HUMAN_CONTROL_TRANSFER_OR_EXPLICIT_AFTER_CONDITION_CHANGE"
            allowed.append("authorized-human-control-transfer")
        elif provider_action == PROVIDER_ACTION_WAIT:
            reentry = "WAIT_FOR_PROVIDER_CONDITION_CHANGE"
            allowed.append("wait-for-provider-condition-change")
        else:
            reentry = "EXPLICIT_AFTER_PROVIDER_CONDITION_CHANGE"
            allowed.append("hold-provider-effect")
    elif standing in PROVIDER_UI_UNRESOLVED_STANDINGS:
        state = "PROVIDER_UI_OR_CONTROL_UNRESOLVED"
        provider_admission = "UNRESOLVED"
        human_verification_eligible = False
        reentry = "EXPLICIT_AFTER_LOCAL_OR_PROVIDER_STATE_CHANGE"
        allowed.append("hold-provider-effect")

    return {
        "schemaVersion": 1,
        "kind": "ordivon.provider-boundary-diagnosis",
        **_policy_metadata(),
        "providerStanding": standing,
        "state": state,
        "substrateStanding": substrate,
        "providerAdmission": provider_admission,
        "providerAction": provider_action,
        "carrierRouting": carrier_routing,
        "humanVerificationEligible": human_verification_eligible,
        "reentry": reentry,
        "automaticInfrastructureMutationAllowed": False,
        "allowedAutomaticActions": allowed,
        "forbiddenAutomaticInfrastructureRepairs": list(_INFRASTRUCTURE_REPAIRS),
    }
