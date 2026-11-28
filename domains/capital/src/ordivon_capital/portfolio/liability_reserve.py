"""Conservative dated cash obligations; no reliance on projected income or asset sales."""

from __future__ import annotations

from datetime import date
from typing import Any

from .strategic_contribution import AllocationPolicyError, _nonnegative_minor


def _calendar_date(value: Any, label: str) -> date:
    if type(value) is not str:
        raise AllocationPolicyError(f"{label}: ISO calendar date required")
    try:
        result = date.fromisoformat(value)
    except ValueError as exc:
        raise AllocationPolicyError(f"{label}: invalid calendar date") from exc
    if result.isoformat() != value:
        raise AllocationPolicyError(f"{label}: canonical YYYY-MM-DD required")
    return result


def project_liability_reserve(
    *, cash_minor: int, emergency_reserve_minor: int, as_of_date: str,
    reserve_through_date: str, obligations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Reserve all outstanding obligations due through an inclusive horizon.

    Past-due outstanding obligations count immediately. Later obligations are
    reported, not treated as covered. No future income, return or asset-sale
    assumptions are permitted. Amounts use the caller's single USD cash ledger.
    """
    cash = _nonnegative_minor(cash_minor, "cashMinor")
    emergency = _nonnegative_minor(emergency_reserve_minor, "emergencyReserveMinor")
    as_of = _calendar_date(as_of_date, "asOfDate")
    horizon = _calendar_date(reserve_through_date, "reserveThroughDate")
    if horizon < as_of:
        raise AllocationPolicyError("reserve horizon precedes as-of date")
    if type(obligations) is not list:
        raise AllocationPolicyError("obligations must be a JSON array")

    seen: set[str] = set()
    covered, deferred = [], []
    due = later = overdue = 0
    for row in obligations:
        if type(row) is not dict or set(row) != {"id", "dueDate", "amountMinor"}:
            raise AllocationPolicyError("invalid outstanding obligation fields")
        identity = row["id"]
        if type(identity) is not str or not identity.strip() or identity in seen:
            raise AllocationPolicyError("obligation id must be nonblank and unique")
        seen.add(identity)
        day = _calendar_date(row["dueDate"], "dueDate")
        amount = _nonnegative_minor(row["amountMinor"], "amountMinor")
        if day <= horizon:
            covered.append(identity)
            due += amount
            if day < as_of:
                overdue += amount
        else:
            deferred.append(identity)
            later += amount
    required = _nonnegative_minor(emergency + due, "requiredReserveMinor")
    _nonnegative_minor(later, "outsideHorizonObligationsMinor")
    return {
        "asOfDate": as_of_date,
        "reserveThroughDate": reserve_through_date,
        "emergencyReserveMinor": emergency,
        "obligationsThroughHorizonMinor": due,
        "overdueMinor": overdue,
        "outsideHorizonObligationsMinor": later,
        "requiredReserveMinor": required,
        "reserveShortfallMinor": max(0, required - cash),
        "availableForContributionMinor": max(0, cash - required),
        "includedObligationIds": sorted(covered),
        "outsideHorizonObligationIds": sorted(deferred),
        "assumptions": "CALLER_DECLARED_OUTSTANDING_OBLIGATIONS_NO_FUTURE_INCOME_OR_SALES",
    }
