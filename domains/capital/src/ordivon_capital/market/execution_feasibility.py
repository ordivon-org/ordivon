from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal, InvalidOperation
from typing import Any


class ExecutionFeasibilityError(ValueError):
    """Unsupported or invalid bounded execution-feasibility input."""


@dataclass(frozen=True)
class BoundedEquitySizingResult:
    quantity: int
    estimated_fee_usd: Decimal
    target_notional_usd: Decimal
    free_portfolio_value_usd: Decimal
    iterations: int


def _d(value: Any, *, name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ExecutionFeasibilityError(f"{name} must be decimal-compatible") from exc
    if not result.is_finite():
        raise ExecutionFeasibilityError(f"{name} must be finite")
    return result


def ib_us_equity_validation_fee(*, quantity: int, price_usd: Any) -> Decimal:
    """LEAN/InteractiveBrokersFeeModel-compatible fee for the frozen US-equity validation lane."""
    if not isinstance(quantity, int) or isinstance(quantity, bool):
        raise ExecutionFeasibilityError("quantity must be an integer number of shares")
    if quantity == 0:
        return Decimal("0")
    price = _d(price_usd, name="price_usd")
    if price <= 0:
        raise ExecutionFeasibilityError("price_usd must be positive")
    q = Decimal(abs(quantity))
    trade_fee = Decimal("0.005") * q
    minimum_fee = Decimal("1")
    maximum_fee = Decimal("0.005") * price * q
    if trade_fee < minimum_fee:
        return minimum_fee
    if trade_fee > maximum_fee:
        return maximum_fee
    return trade_fee


def bounded_us_equity_target_quantity(
    *,
    portfolio_value_usd: Any,
    price_usd: Any,
    target_weight: Any,
    free_portfolio_value_weight: Any,
    current_quantity: int = 0,
    lot_size: int = 1,
) -> BoundedEquitySizingResult:
    """
    Reproduce the qualified LEAN sizing contract for an empty US-equity validation portfolio.

    This intentionally does not claim to implement LEAN's general buying-power model.
    The admitted contract is: positive long target, no existing holding, whole-share lot,
    USD account/security, default LEAN US-equity IB-style fee model, and no additional
    required-free-buying-power percentage beyond the explicit portfolio buffer.
    """
    portfolio_value = _d(portfolio_value_usd, name="portfolio_value_usd")
    price = _d(price_usd, name="price_usd")
    weight = _d(target_weight, name="target_weight")
    buffer_weight = _d(
        free_portfolio_value_weight, name="free_portfolio_value_weight"
    )

    if portfolio_value <= 0:
        raise ExecutionFeasibilityError("portfolio_value_usd must be positive")
    if price <= 0:
        raise ExecutionFeasibilityError("price_usd must be positive")
    if weight <= 0 or weight > 1:
        raise ExecutionFeasibilityError("target_weight must be in (0, 1]")
    if buffer_weight < 0 or buffer_weight >= 1:
        raise ExecutionFeasibilityError(
            "free_portfolio_value_weight must be in [0, 1)"
        )
    if current_quantity != 0:
        raise ExecutionFeasibilityError(
            "current_quantity must be zero for the admitted bounded contract"
        )
    if lot_size != 1:
        raise ExecutionFeasibilityError(
            "lot_size must be one share for the admitted bounded contract"
        )

    factor = (Decimal("1") - buffer_weight) * weight
    free_value = portfolio_value * buffer_weight
    target_notional = portfolio_value * factor
    quantity = int((target_notional / price).to_integral_value(rounding=ROUND_DOWN))
    if quantity == 0:
        return BoundedEquitySizingResult(
            quantity=0,
            estimated_fee_usd=Decimal("0"),
            target_notional_usd=target_notional,
            free_portfolio_value_usd=free_value,
            iterations=0,
        )

    for iteration in range(1, 17):
        fee = ib_us_equity_validation_fee(quantity=quantity, price_usd=price)
        fee_adjusted_target = (portfolio_value - fee) * factor
        next_quantity = int(
            (fee_adjusted_target / price).to_integral_value(rounding=ROUND_DOWN)
        )
        if next_quantity == quantity:
            return BoundedEquitySizingResult(
                quantity=quantity,
                estimated_fee_usd=fee,
                target_notional_usd=target_notional,
                free_portfolio_value_usd=free_value,
                iterations=iteration,
            )
        quantity = next_quantity

    raise ExecutionFeasibilityError("bounded equity sizing failed to converge")
