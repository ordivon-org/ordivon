"""Broker margin and declared liquidation events: read-only evidence, not orders.

The segment calculation consumes *provider reported* maintenance and equity.
The long-only sale replay checks cash/debt/share conservation using caller
reported fills; it does not guess a broker's liquidation trigger, timing,
order selection, house margin adjustment or intraday fill.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from .risk_values import (
    PortfolioRiskError,
    _add_exact,
    _d,
    _fmt_lossless,
    _multiply_exact,
)

_ZERO = Decimal("0")


def _number(value: Any, name: str, *, nonnegative: bool = False) -> Decimal:
    if isinstance(value, bool):
        raise PortfolioRiskError(f"{name} cannot be boolean")
    result = _d(value, name)
    if nonnegative and result < _ZERO:
        raise PortfolioRiskError(f"{name} must be nonnegative")
    return result


def _sum_exact(numbers: Sequence[Decimal]) -> Decimal:
    value = _ZERO
    for number in numbers:
        value = _add_exact(value, number)
    return value


def _utc(instant: datetime) -> str:
    if not isinstance(instant, datetime) or instant.tzinfo is None or instant.utcoffset() is None:
        raise PortfolioRiskError("broker observation requires timezone-aware instant")
    return instant.astimezone(UTC).isoformat()


def assess_provider_margin_segments(
    *,
    observed_at: datetime,
    provider: str,
    segments: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compare reported per-segment broker equity and maintenance requirement.

    Unlike an account-wide scalar cushion, a positive total cannot cancel a
    breached individual securities or commodities segment. No broker event
    is inferred solely from a negative margin cushion.
    """
    instant = _utc(observed_at)
    if not isinstance(provider, str) or not provider.strip():
        raise PortfolioRiskError("provider identity is required")
    if not isinstance(segments, (list, tuple)) or not segments:
        raise PortfolioRiskError("one or more explicitly observed segments required")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(segments):
        if not isinstance(row, Mapping) or set(row) != {
            "segmentId", "equityBasis", "marginEquityUsd",
            "initialMarginUsd", "maintenanceMarginUsd",
        }:
            raise PortfolioRiskError(f"segments[{index}] invalid provider field set")
        ident = row["segmentId"]
        basis = row["equityBasis"]
        if (
            not isinstance(ident, str) or not ident.strip()
            or ident in seen or not isinstance(basis, str) or not basis.strip()
        ):
            raise PortfolioRiskError("unique segment identity and equity basis required")
        seen.add(ident)
        equity = _number(row["marginEquityUsd"], f"{ident}.marginEquityUsd")
        initial = _number(row["initialMarginUsd"], f"{ident}.initialMarginUsd", nonnegative=True)
        required = _number(
            row["maintenanceMarginUsd"], f"{ident}.maintenanceMarginUsd", nonnegative=True,
        )
        excess = _add_exact(equity, -required)
        available = _add_exact(equity, -initial)
        out.append({
            "segmentId": ident,
            "equityBasis": basis,
            "reportedMarginEquityUsd": _fmt_lossless(equity),
            "reportedInitialMarginUsd": _fmt_lossless(initial),
            "reportedMaintenanceMarginUsd": _fmt_lossless(required),
            "availableFundsUsd": _fmt_lossless(available),
            "excessLiquidityUsd": _fmt_lossless(excess),
            "maintenanceBreached": excess < _ZERO,
        })
    return {
        "standing": "CALLER_SUPPLIED_BROKER_SNAPSHOT_NOT_INDEPENDENTLY_ATTESTED",
        "effectStanding": "READ_ONLY_NO_ORDERS_NO_PAPER_LEDGER",
        "provider": provider.strip(),
        "observedAtUtc": instant,
        "anySegmentMaintenanceBreached": any(x["maintenanceBreached"] for x in out),
        "segments": out,
        "limitation": (
            "No broker liquidation is asserted by this state calculation. "
            "A safe-looking aggregated excess cannot erase a violated segment."
        ),
    }


def replay_declared_long_liquidation(
    *,
    observed_at: datetime,
    positions: Sequence[Mapping[str, Any]],
    fills: Sequence[Mapping[str, Any]],
    cash_before_usd: Any,
    loan_before_usd: Any,
    loan_repayment_usd: Any,
    provider_maintenance_before_usd: Any,
    provider_maintenance_after_usd: Any,
) -> dict[str, Any]:
    """Reconcile long-only declared forced-sale fills with exact asset/debt flows.

    Holdings are valued at one fixed caller-supplied reference mark BEFORE
    and AFTER the fills. A sold quantity moves at actual supplied fill price,
    not that reference mark. Other intraday price moves and brokerage
    house-margin revaluation are NOT guessed. Zero or negative equity and
    unpaid loan residuals remain representable: not a forced zero-loss floor.
    """
    instant = _utc(observed_at)
    if not isinstance(positions, (list, tuple)) or not positions:
        raise PortfolioRiskError("nonempty explicit marked holdings required")
    if not isinstance(fills, (list, tuple)) or not fills:
        raise PortfolioRiskError("nonempty declared liquidation fill events required")
    cash = _number(cash_before_usd, "cash_before_usd", nonnegative=True)
    loan = _number(loan_before_usd, "loan_before_usd", nonnegative=True)
    paydown = _number(loan_repayment_usd, "loan_repayment_usd", nonnegative=True)
    before_maintenance = _number(
        provider_maintenance_before_usd, "provider_maintenance_before_usd", nonnegative=True,
    )
    after_maintenance = _number(
        provider_maintenance_after_usd, "provider_maintenance_after_usd", nonnegative=True,
    )
    if paydown > loan:
        raise PortfolioRiskError("debt repayment cannot exceed outstanding loan")
    inventory: dict[str, tuple[Decimal, Decimal]] = {}
    for i, row in enumerate(positions):
        if not isinstance(row, Mapping) or set(row) != {
            "instrumentId", "quantity", "markPriceUsd",
        }:
            raise PortfolioRiskError(f"positions[{i}] invalid field set")
        instrument = row["instrumentId"]
        if not isinstance(instrument, str) or not instrument.strip() or instrument in inventory:
            raise PortfolioRiskError("unique position identity required")
        qty = _number(row["quantity"], f"{instrument}.quantity", nonnegative=True)
        mark = _number(row["markPriceUsd"], f"{instrument}.markPriceUsd")
        if mark <= _ZERO:
            raise PortfolioRiskError("reference mark must be positive")
        inventory[instrument] = (qty, mark)
    before_assets = _sum_exact([
        _multiply_exact(q, mark) for q, mark in inventory.values()
    ])
    before_equity = _add_exact(_add_exact(before_assets, cash), -loan)
    sale_proceeds = _ZERO
    fees = _ZERO
    slippage = _ZERO
    remaining = {key: pair[0] for key, pair in inventory.items()}
    for i, fill in enumerate(fills):
        if not isinstance(fill, Mapping) or set(fill) != {
            "instrumentId", "sellQuantity", "fillPriceUsd", "feeUsd",
        }:
            raise PortfolioRiskError(f"fills[{i}] invalid field set")
        instrument = fill["instrumentId"]
        if not isinstance(instrument, str) or instrument not in inventory:
            raise PortfolioRiskError("fill must reference an existing long holding")
        qty = _number(fill["sellQuantity"], f"fills[{i}].sellQuantity")
        price = _number(fill["fillPriceUsd"], f"fills[{i}].fillPriceUsd")
        fee = _number(fill["feeUsd"], f"fills[{i}].feeUsd", nonnegative=True)
        if qty <= _ZERO or price <= _ZERO or qty > remaining[instrument]:
            raise PortfolioRiskError("fill quantity or price invalid or oversells inventory")
        remaining[instrument] = _add_exact(remaining[instrument], -qty)
        mark = inventory[instrument][1]
        sale_proceeds = _add_exact(sale_proceeds, _multiply_exact(qty, price))
        fees = _add_exact(fees, fee)
        slippage = _add_exact(
            slippage, _multiply_exact(qty, _add_exact(price, -mark))
        )
    available_cash = _add_exact(_add_exact(cash, sale_proceeds), -fees)
    if paydown > available_cash or available_cash < _ZERO:
        raise PortfolioRiskError(
            "declared fill and loan paydown require unavailable cash; "
            "future 1r deposits cannot rescue the prior event"
        )
    after_cash = _add_exact(available_cash, -paydown)
    after_loan = _add_exact(loan, -paydown)
    after_assets = _sum_exact([
        _multiply_exact(remaining[key], mark) for key, (_, mark) in inventory.items()
    ])
    after_equity = _add_exact(_add_exact(after_assets, after_cash), -after_loan)
    realized_loss = _add_exact(slippage, -fees)
    actual_delta = _add_exact(after_equity, -before_equity)
    if actual_delta != realized_loss:
        raise PortfolioRiskError("liquidation self-financing identity failed")
    before_gap = _add_exact(before_equity, -before_maintenance)
    after_gap = _add_exact(after_equity, -after_maintenance)
    return {
        "standing": "DECLARED_LONG_ONLY_LIQUIDATION_REPLAY_NOT_BROKER_ATTESTED",
        "effectStanding": "READ_ONLY_NO_ORDERS_NO_PAPER_LEDGER",
        "observedAtUtc": instant,
        "equityBasis": "FIXED_MARK_LONG_ONLY_CASH_MINUS_LOAN_NOT_PROVIDER_EWL",
        "beforeEquityUsd": _fmt_lossless(before_equity),
        "afterEquityUsd": _fmt_lossless(after_equity),
        "beforeMaintenanceGapUsd": _fmt_lossless(before_gap),
        "afterMaintenanceGapUsd": _fmt_lossless(after_gap),
        "beforeMaintenanceBreached": before_gap < _ZERO,
        "afterMaintenanceBreached": after_gap < _ZERO,
        "cashAfterUsd": _fmt_lossless(after_cash),
        "loanAfterUsd": _fmt_lossless(after_loan),
        "remainingUncoveredNetLiabilityUsd": _fmt_lossless(max(_ZERO, -after_equity)),
        "realizedExecutionPriceDifferenceUsd": _fmt_lossless(slippage),
        "feesUsd": _fmt_lossless(fees),
        "equityChangeUsd": _fmt_lossless(actual_delta),
        "selfFinancingResidualUsd": "0",
        "remainingQuantities": {
            key: _fmt_lossless(quantity) for key, quantity in remaining.items()
        },
        "limitations": [
            "The caller supplies fills; this model does not choose a liquidation time, order or fill.",
            "Broker EWL, segregated collateral, corporate actions and maintenance changes require authenticated provider evidence.",
            "Only one-currency long-only shares at a common reference mark; no intraday remark or additional external cashflow.",
            "A sold position need not restore compliance; any remaining loan or negative net equity remains recorded.",
        ],
    }
