"""Pure Risk LEGO: compare observable exposures with declared numeric risk limits.

No file, credential, execution policy, market provider, or order mutation is needed.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from .risk_values import PortfolioRiskError

DECISION_IMPLEMENTATION = "LOCAL_DETERMINISTIC_PYTHON"


def _amount(value: Any) -> Decimal:
    try:
        result = Decimal(str(value))
        if not result.is_finite():
            raise InvalidOperation
        return result
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise PortfolioRiskError(f"invalid decimal risk fact: {value!r}") from exc


def _limit_decision(facts: dict[str, Any]) -> dict[str, Any]:
    if facts["complete"] is False:
        return {
            "standing": "INCOMPLETE",
            "missingBudgetInputs": facts["missingBudgetInputs"],
            "statuses": {},
        }
    statuses = {
        "MAX_GROSS_TO_EQUITY": (
            "PASS" if facts["grossToEquity"] <= facts["maxGrossToEquity"] else "FAIL"
        ),
        "MAX_LARGEST_POSITION_GROSS_SHARE": (
            "PASS"
            if facts["largestPositionGrossShare"] <= facts["maxLargestPositionGrossShare"]
            else "FAIL"
        ),
        "MIN_AVAILABLE_EQUITY_RATIO": (
            "PASS" if facts["availableEquityRatio"] >= facts["minAvailableEquityRatio"] else "FAIL"
        ),
        "MAX_EQUITY_LOSS_AT_NAMED_SHOCK": (
            "PASS" if facts["shockLossPct"] <= facts["maxEquityLossPctAtShock"] else "FAIL"
        ),
    }
    return {
        "standing": (
            "SATISFIED" if all(value == "PASS" for value in statuses.values()) else "BREACHED"
        ),
        "missingBudgetInputs": [],
        "statuses": statuses,
    }


def evaluate_risk_limits(
    *,
    exposure_ledger: dict[str, Any],
    budget: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate explicit financial exposure limits; no execution policy or broker access."""

    required = (
        "maxGrossToEquity",
        "maxLargestPositionGrossShare",
        "minAvailableEquityRatio",
        "shockMagnitudePct",
        "maxEquityLossPctAtShock",
    )
    missing = [key for key in required if budget.get(key) is None]
    if missing:
        decision = _limit_decision({"complete": False, "missingBudgetInputs": missing})
        return {
            "schemaVersion": 2,
            "kind": "ordivon.capital.governance.risk-limit-evaluation",
            "componentId": "risk-limit-evaluator",
            "decisionImplementation": DECISION_IMPLEMENTATION,
            "standing": decision["standing"],
            "missingBudgetInputs": decision["missingBudgetInputs"],
        }

    max_gross = _amount(budget["maxGrossToEquity"])
    max_concentration = _amount(budget["maxLargestPositionGrossShare"])
    min_available = _amount(budget["minAvailableEquityRatio"])
    shock_pct = _amount(budget["shockMagnitudePct"])
    max_loss_pct = _amount(budget["maxEquityLossPctAtShock"])
    if max_gross <= 0:
        raise PortfolioRiskError("budget.maxGrossToEquity must be positive")
    if max_concentration <= 0 or max_concentration > 1:
        raise PortfolioRiskError("budget.maxLargestPositionGrossShare must be in (0, 1]")
    if min_available < 0 or min_available > 1:
        raise PortfolioRiskError("budget.minAvailableEquityRatio must be in [0, 1]")
    if shock_pct <= 0 or shock_pct > 100:
        raise PortfolioRiskError("budget.shockMagnitudePct must be in (0, 100]")
    if max_loss_pct <= 0 or max_loss_pct > 100:
        raise PortfolioRiskError("budget.maxEquityLossPctAtShock must be in (0, 100]")

    gross_to_equity = _amount(exposure_ledger.get("grossToEquity"))
    concentration = _amount(exposure_ledger.get("largestPositionGrossShare"))
    available_ratio = _amount(exposure_ledger.get("availableEquityRatio"))
    positions = exposure_ledger.get("positions")
    if not isinstance(positions, list):
        raise PortfolioRiskError("ledger.positions must be a list")
    largest_equity_multiple = max(
        (_amount(row.get("equityMultiple")) for row in positions),
        default=Decimal("0"),
    )
    shock_loss_pct = largest_equity_multiple * shock_pct
    decision = _limit_decision(
        {
            "complete": True,
            "missingBudgetInputs": [],
            "grossToEquity": gross_to_equity,
            "maxGrossToEquity": max_gross,
            "largestPositionGrossShare": concentration,
            "maxLargestPositionGrossShare": max_concentration,
            "availableEquityRatio": available_ratio,
            "minAvailableEquityRatio": min_available,
            "shockLossPct": shock_loss_pct,
            "maxEquityLossPctAtShock": max_loss_pct,
        }
    )

    rows = [
        ("MAX_GROSS_TO_EQUITY", gross_to_equity, max_gross, None),
        ("MAX_LARGEST_POSITION_GROSS_SHARE", concentration, max_concentration, None),
        ("MIN_AVAILABLE_EQUITY_RATIO", available_ratio, min_available, None),
        ("MAX_EQUITY_LOSS_AT_NAMED_SHOCK", shock_loss_pct, max_loss_pct, shock_pct),
    ]
    checks = []
    for check_id, observed, limit, shock in rows:
        status = decision["statuses"][check_id]
        row = {
            "id": check_id,
            "observed": format(observed.quantize(Decimal("0.000001")), "f"),
            "limit": format(limit.quantize(Decimal("0.000001")), "f"),
            "passed": status == "PASS",
        }
        if shock is not None:
            row["shockMagnitudePct"] = format(shock.quantize(Decimal("0.000001")), "f")
        checks.append(row)
    breached = [row["id"] for row in checks if not row["passed"]]
    return {
        "schemaVersion": 2,
        "kind": "ordivon.capital.governance.risk-limit-evaluation",
        "componentId": "risk-limit-evaluator",
        "decisionImplementation": DECISION_IMPLEMENTATION,
        "standing": decision["standing"],
        "checks": checks,
        "breachedChecks": breached,
    }
