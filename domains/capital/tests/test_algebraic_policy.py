"""Independent economic contract checks for the algebraic portfolio problem.

Numerical values here are mathematical counterexample/witness fixtures, not
recommended allocations, risk budgets, loan rates or market forecasts.
"""
from __future__ import annotations

import math

import pytest

from ordivon_capital.portfolio.algebraic_policy import (
    AlgebraicPolicyError,
    OnePeriodProblem,
    Scenario,
    merton_single_risky_crra,
    solve_one_period,
    unitize_external_contribution,
)


def one_asset(
    *, returns: tuple[float, ...], probs: tuple[float, ...],
    gamma: float, initial: float,
    maintenance: tuple[float, ...], cash: float, debt: float,
    turnover: float = 0, previous: float = 0,
) -> OnePeriodProblem:
    return OnePeriodProblem(
        gamma=gamma,
        initial_margin=(initial,),
        turnover_cost=(turnover,),
        old_weights=(previous,),
        scenarios=tuple(
            Scenario(p, (g,), cash, debt, (m,))
            for p, g, m in zip(probs, returns, maintenance, strict=True)
        ),
    )


def test_crra_merton_interior_and_lending_borrowing_kink() -> None:
    a = {
        "cash_rate": .02, "borrowing_rate": .05,
        "variance": .04, "gamma": 2,
    }
    assert merton_single_risky_crra(expected_return=-.01, **a) == 0
    assert merton_single_risky_crra(expected_return=.03, **a) == pytest.approx(.125)
    assert merton_single_risky_crra(expected_return=.11, **a) == 1.0
    assert merton_single_risky_crra(expected_return=.18, **a) == pytest.approx(1.625)
    with pytest.raises(AlgebraicPolicyError):
        merton_single_risky_crra(
            expected_return=.1, cash_rate=.06, borrowing_rate=.01,
            variance=.04, gamma=2,
        )


def test_unit_r_contribution_changes_units_not_time_weighted_nav() -> None:
    u, outstanding = unitize_external_contribution(
        unit_nav_before=5, outstanding_units=2, contribution_r=3
    )
    assert u == 5
    assert outstanding == pytest.approx(2.6)
    assert u * outstanding == pytest.approx(2 * 5 + 3)
    # Positive homogeneity: both existing assets and new flow scale.
    u2, outstanding2 = unitize_external_contribution(
        unit_nav_before=5, outstanding_units=2 * 9, contribution_r=3 * 9
    )
    assert u2 == u
    assert outstanding2 == pytest.approx(9 * outstanding)


def test_dominated_risky_asset_optimal_hold_cash_no_magic_leverage() -> None:
    problem = one_asset(
        returns=(.7, .9), probs=(.5, .5),
        gamma=3, initial=.5, maintenance=(.25, .3),
        cash=1.02, debt=1.04,
    )
    result = solve_one_period(problem)
    assert result.standing == "SCENARIO_OPTIMUM_NOT_FORWARD_VERIFIED"
    assert result.risky_weights[0] == pytest.approx(0, abs=1e-6)
    assert result.cash_weight == pytest.approx(1, abs=1e-6)
    assert result.debt_weight == pytest.approx(0, abs=1e-6)
    assert result.certainty_equivalent == pytest.approx(1.02, abs=1e-6)
    assert result.numerical_residual < 1e-7


def test_expected_growth_and_actual_broker_margin_determine_borrowing() -> None:
    problem = one_asset(
        returns=(1.8, 2.0), probs=(.4, .6),
        gamma=1, initial=.4, maintenance=(.2, .2),
        cash=1.0, debt=1.01,
    )
    result = solve_one_period(problem)
    exposure = result.risky_weights[0]
    assert exposure > 1
    assert result.cash_weight == pytest.approx(0, abs=1e-6)
    assert result.debt_weight == pytest.approx(exposure - 1, abs=1e-5)
    assert .4 * exposure <= 1 + 1e-7
    assert result.post_trade_equity == pytest.approx(1)
    for wealth, scenario in zip(result.scenario_equities, problem.scenarios):
        assert wealth >= exposure * scenario.risky_gross_returns[0] * scenario.maintenance[0] - 1e-7


def test_scenario_maintenance_restricts_optimal_exposure_and_costs_are_real() -> None:
    problem = one_asset(
        returns=(.2, 2.0), probs=(.05, .95),
        gamma=1, initial=.4, maintenance=(.7, .4),
        cash=1.01, debt=1.04, turnover=.02,
    )
    result = solve_one_period(problem)
    w = result.risky_weights[0]
    assert result.transaction_cost == pytest.approx(.02 * abs(w), abs=1e-6)
    assert result.post_trade_equity == pytest.approx(1 - result.transaction_cost, abs=1e-6)
    assert sum(result.risky_weights) + result.cash_weight - result.debt_weight + result.transaction_cost == pytest.approx(1, abs=1e-6)
    assert .4 * w <= result.post_trade_equity + 1e-6
    assert result.numerical_residual < 1e-7
    for wealth, scenario in zip(result.scenario_equities, problem.scenarios):
        assert wealth >= scenario.maintenance[0] * w * scenario.risky_gross_returns[0] - 1e-6


def test_reject_unknown_probability_distribution_and_unknown_utility() -> None:
    original = one_asset(
        returns=(.7, 1.2), probs=(.5, .5), gamma=1,
        initial=.5, maintenance=(.2, .2), cash=1, debt=1,
    )
    with pytest.raises(AlgebraicPolicyError):
        solve_one_period(OnePeriodProblem(
            gamma=math.nan, initial_margin=original.initial_margin,
            turnover_cost=original.turnover_cost, old_weights=original.old_weights,
            scenarios=original.scenarios,
        ))
    with pytest.raises(AlgebraicPolicyError, match="probabilities"):
        solve_one_period(OnePeriodProblem(
            gamma=2, initial_margin=original.initial_margin,
            turnover_cost=original.turnover_cost, old_weights=original.old_weights,
            scenarios=(
                Scenario(.3, (.7,), 1, 1, (.2,)),
                Scenario(.3, (1.2,), 1, 1, (.2,)),
            ),
        ))
