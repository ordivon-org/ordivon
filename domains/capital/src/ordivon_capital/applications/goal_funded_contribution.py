"""Compose dated liquidity protection with the existing read-only allocator."""

from __future__ import annotations

from typing import Any

from ..portfolio.liability_reserve import project_liability_reserve
from ..portfolio.strategic_contribution import (
    AllocationPolicyError,
    _nonnegative_minor,
    plan_strategic_contribution,
)

REQUEST_KIND = "ordivon.finance.portfolio.goal-funded-contribution-request"
_FIELDS = {
    "schemaVersion", "kind", "currency", "cashMinor", "contributionMinor",
    "holdingsMinor", "targetWeightsBps", "asOfDate", "reserveThroughDate",
    "emergencyReserveMinor", "obligations",
}


def plan_goal_funded_contribution(request: dict[str, Any]) -> dict[str, Any]:
    if type(request) is not dict or set(request) != _FIELDS:
        raise AllocationPolicyError("invalid goal-funded request fields")
    if type(request["schemaVersion"]) is not int or request["schemaVersion"] != 1:
        raise AllocationPolicyError("schemaVersion must be exactly 1")
    if request["kind"] != REQUEST_KIND:
        raise AllocationPolicyError("unexpected goal-funded request kind")
    cash = _nonnegative_minor(request["cashMinor"], "cashMinor")
    desired = _nonnegative_minor(request["contributionMinor"], "contributionMinor")
    reserve = project_liability_reserve(
        cash_minor=cash, emergency_reserve_minor=request["emergencyReserveMinor"],
        as_of_date=request["asOfDate"], reserve_through_date=request["reserveThroughDate"],
        obligations=request["obligations"],
    )
    amount = min(desired, reserve["availableForContributionMinor"])
    shortfall = reserve["reserveShortfallMinor"]
    # Validate the existing allocation inputs even when no allocation is possible.
    allocation = plan_strategic_contribution({
        "schemaVersion": 1,
        "kind": "ordivon.finance.portfolio.strategic-contribution-request",
        "currency": request["currency"], "cashMinor": cash,
        "protectedReserveMinor": min(cash, reserve["requiredReserveMinor"]),
        "contributionMinor": amount, "holdingsMinor": request["holdingsMinor"],
        "targetWeightsBps": request["targetWeightsBps"],
    })
    return {
        "schemaVersion": 1,
        "kind": "ordivon.finance.portfolio.goal-funded-contribution-plan",
        "standing": (
            "RESERVE_SHORTFALL" if shortfall else
            "CONTRIBUTION_CAPPED" if amount < desired else "READ_ONLY_PROJECTION"
        ),
        "currency": request["currency"],
        "requestedContributionMinor": desired,
        "projectedContributionMinor": amount,
        "unallocatedRequestedContributionMinor": desired - amount,
        "liquidityReserve": reserve,
        "allocationPlan": None if shortfall else allocation,
        "dataStanding": "CALLER_SUPPLIED_UNATTESTED",
        "riskStanding": "NOT_EVALUATED",
        "executionAuthorized": False,
    }
