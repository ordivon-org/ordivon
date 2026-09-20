#!/usr/bin/env python3
"""Pure Provider Boundary diagnosis and repair-routing policy for Agent Automation.

This module classifies one read-only provider preflight observation. It does not access the
provider, Browserless, the network, profile state, or any external effect. The classifier keeps
carrier/transport failover separate from provider-policy/UI blockers and explicitly prevents
provider-boundary observations from being reinterpreted as infrastructure repair instructions.

The Browser Security R9 reference is a knowledge-policy reference only. It is not a live assertion
that current neutral presentation has been re-measured on every preflight.
"""

from __future__ import annotations

from typing import Any

POLICY_VERSION = "provider-boundary-r1"
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

HUMAN_VERIFICATION_ELIGIBLE_STANDINGS = frozenset(
    {
        "CHALLENGE_GATED",
        "AUTH_REQUIRED",
    }
)

_INFRASTRUCTURE_REPAIRS = (
    "rotate-carrier",
    "restart-carrier",
    "clear-profile",
    "mutate-launcher-flags",
    "mutate-network-authority",
)


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
    """Static policy projection suitable for doctor/operations output."""
    return {
        "schemaVersion": 1,
        "kind": "ordivon.provider-boundary-policy",
        **_policy_metadata(),
        "automaticInfrastructureMutationFromProviderBoundary": False,
        "carrierFailoverStandings": sorted(CARRIER_FAILOVER_STANDINGS),
        "providerNotAdmissibleStandings": sorted(PROVIDER_NOT_ADMISSIBLE_STANDINGS),
        "providerUiUnresolvedStandings": sorted(PROVIDER_UI_UNRESOLVED_STANDINGS),
        "forbiddenAutomaticInfrastructureRepairs": list(_INFRASTRUCTURE_REPAIRS),
    }


def diagnose_provider_preflight(observation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(observation, dict):
        raise ValueError("provider preflight observation must be an object")
    standing = observation.get("standing")
    if not isinstance(standing, str) or not standing:
        raise ValueError("provider preflight standing is required")

    substrate = _substrate_standing(observation)
    carrier_routing = "PRESERVE_SELECTED_CARRIER"
    provider_admission = "UNRESOLVED"
    human_verification_eligible = standing in HUMAN_VERIFICATION_ELIGIBLE_STANDINGS
    reentry = "EXPLICIT_AFTER_CONDITION_CHANGE"
    allowed = ["record-telemetry", "preserve-selected-carrier"]
    state = "PREFLIGHT_UNRESOLVED"

    if standing in CARRIER_FAILOVER_STANDINGS:
        state = "CARRIER_PRE_EFFECT_UNAVAILABLE"
        carrier_routing = "FAILOVER_ALLOWED"
        provider_admission = "NOT_OBSERVED"
        human_verification_eligible = False
        reentry = "TRY_NEXT_CARRIER"
        allowed = ["record-telemetry", "try-next-carrier"]
    elif standing == "READY":
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
        if human_verification_eligible:
            reentry = "HUMAN_VERIFICATION_OR_EXPLICIT_AFTER_CONDITION_CHANGE"
            allowed.append("human-verification")
        else:
            reentry = "WAIT_FOR_PROVIDER_CONDITION_CHANGE"
            allowed.append("wait-for-provider-condition-change")
    elif standing in PROVIDER_UI_UNRESOLVED_STANDINGS:
        state = "PROVIDER_UI_OR_CONTROL_UNRESOLVED"
        provider_admission = "UNRESOLVED"
        human_verification_eligible = False
        reentry = "EXPLICIT_AFTER_LOCAL_OR_PROVIDER_STATE_CHANGE"

    diagnosis = {
        "schemaVersion": 1,
        "kind": "ordivon.provider-boundary-diagnosis",
        **_policy_metadata(),
        "providerStanding": standing,
        "state": state,
        "substrateStanding": substrate,
        "providerAdmission": provider_admission,
        "carrierRouting": carrier_routing,
        "humanVerificationEligible": human_verification_eligible,
        "reentry": reentry,
        "automaticInfrastructureMutationAllowed": False,
        "allowedAutomaticActions": allowed,
        "forbiddenAutomaticInfrastructureRepairs": list(_INFRASTRUCTURE_REPAIRS),
    }
    return diagnosis
