from __future__ import annotations

from decimal import Decimal

import pytest

from ordivon_capital.trading.execution_feasibility import (
    ExecutionFeasibilityError,
    bounded_us_equity_target_quantity,
    ib_us_equity_validation_fee,
)

WEIGHT = Decimal("0.3333333333333333")


@pytest.mark.parametrize(
    ("price", "expected"),
    [
        ("332.27", 99),
        ("495.63", 66),
        ("218.29", 151),
    ],
)
def test_shadow_precommit_quantities_match_latest_lean(price, expected):
    result = bounded_us_equity_target_quantity(
        portfolio_value_usd="100000",
        price_usd=price,
        target_weight=WEIGHT,
        free_portfolio_value_weight="0.01",
    )
    assert result.quantity == expected


@pytest.mark.parametrize(
    ("price", "expected"),
    [
        ("10.00", 3332),
        ("10.01", 3329),
        ("11.23", 2967),
    ],
)
def test_low_price_boundary_includes_fee_iteration(price, expected):
    result = bounded_us_equity_target_quantity(
        portfolio_value_usd="100000",
        price_usd=price,
        target_weight=WEIGHT,
        free_portfolio_value_weight="0",
    )
    assert result.quantity == expected
    assert result.iterations >= 2


def test_ib_equity_fee_matches_frozen_lean_fee_schedule():
    assert ib_us_equity_validation_fee(quantity=99, price_usd="332.27") == Decimal("1")
    assert ib_us_equity_validation_fee(quantity=3333, price_usd="10") == Decimal(
        "16.665"
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"current_quantity": 1}, "current_quantity must be zero"),
        ({"lot_size": 100}, "lot_size must be one share"),
        ({"price_usd": "0"}, "price_usd must be positive"),
        ({"target_weight": "0"}, "target_weight must be in"),
        ({"free_portfolio_value_weight": "1"}, "free_portfolio_value_weight"),
    ],
)
def test_out_of_contract_inputs_fail_closed(kwargs, message):
    args = {
        "portfolio_value_usd": "100000",
        "price_usd": "100",
        "target_weight": WEIGHT,
        "free_portfolio_value_weight": "0.01",
    }
    args.update(kwargs)
    with pytest.raises(ExecutionFeasibilityError, match=message):
        bounded_us_equity_target_quantity(**args)
