"""Deterministic contribution-only allocation projection, not a trading engine.

Ownership: Portfolio calculates a user's given target weights and capital envelope.
Risk/Governance/Trading retain independent risk, admission and execution authority.
All amounts are exact nonnegative integer USD minor units (cents).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

_MAX_MINOR = 2**63 - 1
_MAX_INSTRUMENTS = 128
_REQUIRED = {
    "schemaVersion",
    "kind",
    "currency",
    "cashMinor",
    "protectedReserveMinor",
    "contributionMinor",
    "holdingsMinor",
    "targetWeightsBps",
}
_ASSET = re.compile(r"[A-Z0-9][A-Z0-9._-]{0,63}\Z")


class AllocationPolicyError(ValueError):
    """The caller-supplied investment policy is not mechanically admissible."""


def _nonnegative_minor(value: Any, name: str) -> int:
    if type(value) is not int or not 0 <= value <= _MAX_MINOR:
        raise AllocationPolicyError(f"{name} must be integer cents in [0, 2^63-1]")
    return value


def _instrument_map(raw: Any, name: str, *, weights: bool) -> dict[str, int]:
    if type(raw) is not dict or not 1 <= len(raw) <= _MAX_INSTRUMENTS:
        raise AllocationPolicyError(f"{name} must be a nonempty bounded asset map")
    values: dict[str, int] = {}
    for symbol, raw_value in raw.items():
        if type(symbol) is not str or not _ASSET.fullmatch(symbol):
            raise AllocationPolicyError(f"{name} has invalid instrument identity")
        if weights:
            if type(raw_value) is not int or not 0 <= raw_value <= 10000:
                raise AllocationPolicyError(f"{name}.{symbol} must be integer basis points")
            values[symbol] = raw_value
        else:
            values[symbol] = _nonnegative_minor(raw_value, f"{name}.{symbol}")
    return {key: values[key] for key in sorted(values)}


def plan_strategic_contribution(request: Mapping[str, Any]) -> dict[str, Any]:
    """Apply contribution-only gap weighting to explicit caller target weights.

    Each asset deficit is max(0, target_after_contribution - current_value),
    computed in exact integer basis-point * cents units. Allocate contribution
    proportionally to deficits, using largest-remainder cent apportionment.
    Existing holdings are never reduced. This produces no orders, predictions,
    prices, tax/cost estimates, or execution authorization.
    """
    if type(request) is not dict:
        raise AllocationPolicyError("request must be a JSON object")
    if set(request) != _REQUIRED:
        raise AllocationPolicyError(
            f"request fields differ: missing={sorted(_REQUIRED - set(request))}, "
            f"extra={sorted(set(request) - _REQUIRED)}"
        )
    if type(request["schemaVersion"]) is not int or request["schemaVersion"] != 1:
        raise AllocationPolicyError("schemaVersion must be exactly 1")
    if request["kind"] != "ordivon.finance.portfolio.strategic-contribution-request":
        raise AllocationPolicyError("unexpected contribution request kind")
    if request["currency"] != "USD":
        raise AllocationPolicyError("this component accepts only USD integer minor units")

    cash = _nonnegative_minor(request["cashMinor"], "cashMinor")
    reserve = _nonnegative_minor(request["protectedReserveMinor"], "protectedReserveMinor")
    amount = _nonnegative_minor(request["contributionMinor"], "contributionMinor")
    if reserve > cash or amount > cash - reserve:
        raise AllocationPolicyError("contribution would spend protected cash reserve")

    holdings = _instrument_map(request["holdingsMinor"], "holdingsMinor", weights=False)
    targets = _instrument_map(request["targetWeightsBps"], "targetWeightsBps", weights=True)
    if holdings.keys() != targets.keys():
        raise AllocationPolicyError("holding and target instrument identities must agree")
    if sum(targets.values()) != 10000:
        raise AllocationPolicyError("target weights must total exactly 10000 bps")
    invested = sum(holdings.values())
    if invested + amount > _MAX_MINOR:
        raise AllocationPolicyError("projected investment amount exceeds integer boundary")

    projected_total = invested + amount
    gaps = {
        symbol: max(0, projected_total * targets[symbol] - holdings[symbol] * 10000)
        for symbol in targets
    }
    denominator = sum(gaps.values())
    allocations = dict.fromkeys(targets, 0)
    if amount:
        if not denominator:
            raise AllocationPolicyError("positive contribution has no target deficit")
        remainders: list[tuple[int, str]] = []
        for symbol in targets:
            quota, remainder = divmod(amount * gaps[symbol], denominator)
            allocations[symbol] = quota
            remainders.append((remainder, symbol))
        leftover = amount - sum(allocations.values())
        for _, symbol in sorted(remainders, key=lambda item: (-item[0], item[1]))[:leftover]:
            allocations[symbol] += 1

    projected = {
        symbol: holdings[symbol] + allocations[symbol] for symbol in targets
    }
    return {
        "schemaVersion": 1,
        "kind": "ordivon.finance.portfolio.strategic-contribution-plan",
        "standing": "READ_ONLY_PROJECTION" if amount else "READ_ONLY_NO_CONTRIBUTION",
        "currency": "USD",
        "unit": "minor",
        "contributionMinor": amount,
        "cashAfterMinor": cash - amount,
        "protectedReserveMinor": reserve,
        "currentHoldingsMinor": holdings,
        "targetWeightsBps": targets,
        "allocationsMinor": allocations,
        "projectedHoldingsMinor": projected,
        "projectedInvestmentMinor": projected_total,
        "allocationMethod": "TARGET_DEFICIT_LARGEST_REMAINDER",
        "dataStanding": "CALLER_SUPPLIED_UNATTESTED",
        "riskStanding": "NOT_EVALUATED",
        "costsAndTaxesModeled": False,
        "investmentAdviceProduced": False,
        "executionAuthorized": False,
    }
