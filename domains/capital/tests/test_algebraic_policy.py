"""Independent economic contract checks for the algebraic portfolio problem.

Numerical values here are mathematical counterexample/witness fixtures, not
recommended allocations, risk budgets, loan rates or market forecasts.
"""
from __future__ import annotations

import math
from dataclasses import replace
from fractions import Fraction

import pytest

from ordivon_capital.portfolio.algebraic_policy import (
    AlgebraicPolicyError,
    OnePeriodProblem,
    OnePeriodSolution,
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


# Solver-independent acceptance specification for the existing public result.
# The tolerance is numerical reconstruction in normalized 1r, not a risk budget.
# No optimizer internals, constraint matrices, or solver status are an oracle.
def assert_one_period_economic_replay(
    problem: OnePeriodProblem, result: OnePeriodSolution
) -> None:
    """Check observable economic identities; not a global optimum certificate."""
    atol = 1e-6
    n = len(problem.initial_margin)
    w = result.risky_weights
    c, b = result.cash_weight, result.debt_weight
    assert len(w) == n
    assert len(result.scenario_equities) == len(problem.scenarios)
    assert all(math.isfinite(x) and x >= -atol for x in (*w, c, b))
    fees = math.fsum(
        k * abs(new - old)
        for k, new, old in zip(problem.turnover_cost, w, problem.old_weights, strict=True)
    )
    assert result.transaction_cost == pytest.approx(fees, abs=atol, rel=0)
    assert math.fsum((*w, c, -b, fees)) == pytest.approx(1.0, abs=atol, rel=0)
    assert result.post_trade_equity == pytest.approx(1.0 - fees, abs=atol, rel=0)
    initial = math.fsum(
        m * x for m, x in zip(problem.initial_margin, w, strict=True)
    )
    assert initial + fees <= 1.0 + atol

    wealth = []
    for scenario, claimed in zip(problem.scenarios, result.scenario_equities, strict=True):
        positions = tuple(
            x * gross for x, gross in zip(w, scenario.risky_gross_returns, strict=True)
        )
        actual = math.fsum(
            (*positions, c * scenario.cash_gross_return, -b * scenario.debt_gross_return)
        )
        maintenance = math.fsum(
            x * m for x, m in zip(positions, scenario.maintenance, strict=True)
        )
        assert math.isfinite(actual) and actual > 0
        assert actual >= maintenance - atol
        assert claimed == pytest.approx(actual, abs=atol, rel=0)
        wealth.append((scenario.probability, actual))

    gamma = problem.gamma
    expected = math.fsum(p * v for p, v in wealth)
    utility = math.fsum(
        p * (math.log(v) if gamma == 1 else math.expm1((1 - gamma) * math.log(v)) / (1 - gamma))
        for p, v in wealth
    )
    ce = (
        math.exp(utility) if gamma == 1
        else math.exp(math.log1p((1 - gamma) * utility) / (1 - gamma))
    )
    assert result.expected_equity == pytest.approx(expected, abs=atol, rel=0)
    assert result.expected_utility == pytest.approx(utility, abs=atol, rel=0)
    assert result.certainty_equivalent == pytest.approx(ce, abs=atol, rel=0)
    assert result.standing == "SCENARIO_OPTIMUM_NOT_FORWARD_VERIFIED"


def _solver_contract_cases() -> tuple[OnePeriodProblem, ...]:
    return (
        one_asset(
            returns=(.7, .9), probs=(.5, .5), gamma=3, initial=.5,
            maintenance=(.25, .3), cash=1.02, debt=1.04,
        ),
        one_asset(
            returns=(1.8, 2.0), probs=(.4, .6), gamma=1, initial=.4,
            maintenance=(.2, .2), cash=1, debt=1.01,
        ),
        one_asset(
            returns=(.2, 2.0), probs=(.05, .95), gamma=1, initial=.4,
            maintenance=(.7, .4), cash=1.01, debt=1.04, turnover=.02,
        ),
        one_asset(
            returns=(.75, 1.3), probs=(.4, .6), gamma=.5, initial=.5,
            maintenance=(.25, .3), cash=1.01, debt=1.04, turnover=.01, previous=.2,
        ),
        OnePeriodProblem(
            gamma=2, initial_margin=(.5, .6), turnover_cost=(.01, .02),
            old_weights=(.2, .1),
            scenarios=(
                Scenario(.4, (.7, 1.1), 1.01, 1.04, (.25, .3)),
                Scenario(.6, (1.4, .9), 1.01, 1.04, (.25, .3)),
            ),
        ),
    )


@pytest.mark.parametrize(
    "problem", _solver_contract_cases(),
    ids=("dominated", "borrow", "maintenance_fee", "fractional_gamma", "two_assets"),
)
def test_public_solver_result_matches_independent_economic_spec(problem: OnePeriodProblem) -> None:
    assert_one_period_economic_replay(problem, solve_one_period(problem))


@pytest.mark.parametrize(
    "field", (
        "risky_weights", "cash_weight", "transaction_cost", "post_trade_equity",
        "scenario_equities", "expected_equity", "expected_utility", "certainty_equivalent",
        "standing",
    ),
)
def test_independent_spec_rejects_forged_success_even_with_zero_residual(field: str) -> None:
    problem = _solver_contract_cases()[2]
    result = solve_one_period(problem)
    assert_one_period_economic_replay(problem, result)
    value = getattr(result, field)
    if field == "standing":
        forged = "FORWARD_VERIFIED"
    elif isinstance(value, tuple):
        forged = (value[0] + .1, *value[1:])
    else:
        forged = value + .1
    with pytest.raises(AssertionError):
        assert_one_period_economic_replay(
            problem, replace(result, **{field: forged, "numerical_residual": 0.0})
        )


@pytest.mark.parametrize(
    "field,value", (
        ("gamma", True), ("probability", True),
        ("initial_margin", (True,)), ("turnover_cost", (False,)),
        ("old_weights", (False,)), ("risky_gross_returns", (True,)),
        ("cash_gross_return", True), ("debt_gross_return", True),
        ("maintenance", (False,)), ("gamma", "2"), ("gamma", 10**400),
    ),
    ids=(
        "bool-gamma", "bool-probability", "bool-initial-margin", "bool-fee",
        "bool-old-weight", "bool-gross-return", "bool-lend", "bool-borrow",
        "bool-maintenance", "numeric-string", "overflowing-integer",
    ),
)
def test_economic_contract_rejects_non_numeric_or_unrepresentable_values(field, value):
    # JSON booleans and numbers have distinct economic meanings even though
    # Python bool is a subclass of int. Numeric strings are not observations.
    scenario = Scenario(1.0, (1.2,), 1.0, 1.04, (.2,))
    problem = OnePeriodProblem(2.0, (.5,), (.01,), (0.0,), (scenario,))
    if field in {"gamma", "initial_margin", "turnover_cost", "old_weights"}:
        invalid = replace(problem, **{field: value})
    else:
        invalid = replace(problem, scenarios=(replace(scenario, **{field: value}),))
    with pytest.raises(AlgebraicPolicyError):
        solve_one_period(invalid)


def test_feasible_economic_replay_is_not_an_optimality_certificate() -> None:
    problem = _solver_contract_cases()[1]
    # Cash-only is admissible, all identities are exact, and even the
    # published standing and residual can be forged without changing them.
    cash_only = OnePeriodSolution(
        risky_weights=(0.0,), cash_weight=1.0, debt_weight=0.0,
        transaction_cost=0.0, post_trade_equity=1.0,
        scenario_equities=(1.0, 1.0), expected_equity=1.0,
        expected_utility=0.0, certainty_equivalent=1.0, numerical_residual=0.0,
    )
    assert_one_period_economic_replay(problem, cash_only)
    # Independent admissible witness: buy one unit, no debt or fees.
    # It strictly dominates cash in both supplied scenarios, so strict
    # monotonicity of CRRA refutes optimality of cash without a solver.
    invest = OnePeriodSolution(
        risky_weights=(1.0,), cash_weight=0.0, debt_weight=0.0,
        transaction_cost=0.0, post_trade_equity=1.0,
        scenario_equities=(1.8, 2.0), expected_equity=.4 * 1.8 + .6 * 2.0,
        expected_utility=.4 * math.log(1.8) + .6 * math.log(2.0),
        certainty_equivalent=math.exp(.4 * math.log(1.8) + .6 * math.log(2.0)),
        numerical_residual=0.0,
    )
    assert_one_period_economic_replay(problem, invest)
    assert all(a > b for a, b in zip(invest.scenario_equities, cash_only.scenario_equities, strict=True))
    assert invest.expected_utility > cash_only.expected_utility

def _integer_crra_tangent_upper_excess(
    problem: OnePeriodProblem, result: OnePeriodSolution, *, discard_dual: bool = False
) -> Fraction:
    """Independent exact-rational check of a proposed LP dual witness.

    Only positive integer gamma and finite binary-rational input fixtures.
    This bounds optimum utility minus utility at the positive tangent point;
    exact feasibility of the floating point result is a separate obligation.
    HiGHS supplies multipliers, not the trusted upper bound.
    """
    from scipy.optimize import linprog

    assert_one_period_economic_replay(problem, result)
    q = Fraction
    gamma = int(problem.gamma)
    assert gamma == problem.gamma and gamma > 0
    m, k, old = (tuple(map(q, v)) for v in (
        problem.initial_margin, problem.turnover_cost, problem.old_weights,
    ))
    n = len(m)
    zero = q(0)
    # Canonical portfolio: cancel simultaneous cash/debt (borrow >= lend).
    # Actual turnover is |w-old|. Margin and budget imply finite boxes
    # w<=1/m, cash<=1, debt<=sum(1/m), turnover<=1/m+old.
    # Relaxing positive wealth to the closed maintenance half-space can
    # only enlarge the set in the linear tangent maximization.
    wmax = tuple(1 / v for v in m)
    box = (*wmax, q(1), sum(wmax), *(a + b for a, b in zip(wmax, old, strict=True)))
    budget = (q(1),) * n + (q(1), q(-1)) + k
    rows = [(*m, zero, zero, *k)]
    rhs = [q(1)]
    for i, prev in enumerate(old):
        for sign in (1, -1):
            row = [zero] * len(box)
            row[i], row[n + 2 + i] = q(sign), q(-1)
            rows.append(tuple(row))
            rhs.append(sign * prev)
    point = (*map(q, result.risky_weights), q(result.cash_weight), q(result.debt_weight))
    gradient = [zero] * len(box)
    tangent_at_point = zero
    for scenario in problem.scenarios:
        gross = tuple(map(q, scenario.risky_gross_returns))
        lend, borrow = q(scenario.cash_gross_return), q(scenario.debt_gross_return)
        assert borrow >= lend > 0
        wealth_row = (*gross, lend, -borrow)
        wealth = sum(a * b for a, b in zip(wealth_row, point, strict=True))
        assert wealth > 0
        maintenance = tuple(map(q, scenario.maintenance))
        rows.append((
            *(g * (v - 1) for g, v in zip(gross, maintenance, strict=True)),
            -lend, borrow, *((zero,) * n),
        ))
        rhs.append(zero)
        factor = q(scenario.probability) / wealth**gamma
        for j, coefficient in enumerate(wealth_row):
            gradient[j] += factor * coefficient
        tangent_at_point += factor * wealth

    # LP proposes a certificate. Reconstruct using independent exact
    # arithmetic; even an inexact dual is safe with finite-box correction.
    proposed = linprog(
        [-float(v) for v in gradient],
        A_ub=[[float(v) for v in row] for row in rows],
        b_ub=list(map(float, rhs)), A_eq=[list(map(float, budget))], b_eq=[1.0],
        bounds=[(0, float(v)) for v in box], method="highs",
    )
    assert proposed.success
    y = tuple(max(zero, -q(float(v))) for v in proposed.ineqlin.marginals)
    lam = -q(float(proposed.eqlin.marginals[0]))
    if discard_dual:
        y, lam = (zero,) * len(rows), zero
    residual = tuple(
        g - lam * a - sum(multiplier * row[j] for multiplier, row in zip(y, rows, strict=True))
        for j, (g, a) in enumerate(zip(gradient, budget, strict=True))
    )
    upper = lam + sum(a * b for a, b in zip(y, rhs, strict=True))
    upper += sum(max(zero, r) * cap for r, cap in zip(residual, box, strict=True))
    return upper - tangent_at_point


@pytest.mark.parametrize("case", (0, 1, 2, 4))
def test_integer_crra_result_has_small_independently_checked_tangent_excess(case: int) -> None:
    problem = _solver_contract_cases()[case]
    result = solve_one_period(problem)
    upper = _integer_crra_tangent_upper_excess(problem, result)
    # Not a portfolio risk budget; solver result still only numerically feasible.
    assert -1e-6 <= float(upper) <= 1e-5
    # Throwing away multipliers must not give an apparently tight certificate.
    assert _integer_crra_tangent_upper_excess(problem, result, discard_dual=True) >= upper


def test_zero_residual_dominated_result_has_no_small_tangent_excess() -> None:
    problem = _solver_contract_cases()[1]
    cash_only = OnePeriodSolution(
        risky_weights=(0.0,), cash_weight=1.0, debt_weight=0.0,
        transaction_cost=0.0, post_trade_equity=1.0,
        scenario_equities=(1.0, 1.0), expected_equity=1.0,
        expected_utility=0.0, certainty_equivalent=1.0, numerical_residual=0.0,
    )
    assert_one_period_economic_replay(problem, cash_only)
    upper = _integer_crra_tangent_upper_excess(problem, cash_only)
    # A known strictly better feasible unit exposure is an independent
    # lower witness for the utility improvement. A claimed upper bound
    # below that witness would be unsound.
    improvement = .4 * math.log(1.8) + .6 * math.log(2.0)
    assert float(upper) >= improvement > .5

@pytest.mark.parametrize("field", ("expected_return", "cash_rate", "borrowing_rate", "variance", "gamma"))
def test_merton_rejects_boolean_economic_scalar(field: str) -> None:
    inputs = dict(expected_return=.1, cash_rate=.02, borrowing_rate=.04, variance=.04, gamma=2)
    inputs[field] = True
    with pytest.raises(AlgebraicPolicyError):
        merton_single_risky_crra(**inputs)


@pytest.mark.parametrize("field", ("unit_nav_before", "outstanding_units", "contribution_r"))
def test_unitization_rejects_boolean_economic_scalar(field: str) -> None:
    inputs = dict(unit_nav_before=1.0, outstanding_units=2.0, contribution_r=3.0)
    inputs[field] = True
    with pytest.raises(AlgebraicPolicyError):
        unitize_external_contribution(**inputs)


def test_merton_finite_inputs_do_not_silently_overflow_intermediate_product() -> None:
    assert merton_single_risky_crra(
        expected_return=1e308, cash_rate=0, borrowing_rate=0, variance=1e308, gamma=2,
    ) == pytest.approx(.5)
    assert merton_single_risky_crra(
        expected_return=1e-300, cash_rate=0, borrowing_rate=0, variance=1e-200, gamma=1e-200,
    ) == pytest.approx(1e100)


def test_unitization_rejects_unrepresentable_output() -> None:
    with pytest.raises(AlgebraicPolicyError):
        unitize_external_contribution(
            unit_nav_before=1e-308, outstanding_units=1, contribution_r=1e308,
        )

@pytest.mark.parametrize(
    "nav,units,flow",
    ((1e308, 0.0, 1e-308), (1.0, 1e20, 1.0)),
    ids=("increment-underflows", "increment-rounded-away"),
)
def test_positive_capital_flow_cannot_disappear_in_unitization(nav, units, flow):
    # Independent exact-rational accounting identity. A nonzero contribution
    # must increase represented units, or the operation is not representable.
    exact = Fraction(units) + Fraction(flow) / Fraction(nav)
    assert exact > Fraction(units)
    assert float(exact) == units
    with pytest.raises(AlgebraicPolicyError):
        unitize_external_contribution(
            unit_nav_before=nav, outstanding_units=units, contribution_r=flow,
        )


@pytest.mark.parametrize(
    "nav,units,flow",
    ((3.0, 0.1, 0.2), (1.0, 2.0, 3.0), (1e-100, 0.0, 1e-200), (7.0, 2.0, 0.0)),
)
def test_unitization_single_rounding_of_exact_economic_identity(nav, units, flow):
    expected = Fraction(units) + Fraction(flow) / Fraction(nav)
    actual_nav, actual_units = unitize_external_contribution(
        unit_nav_before=nav, outstanding_units=units, contribution_r=flow,
    )
    assert actual_nav == nav
    assert actual_units == float(expected)
    assert math.isfinite(actual_units)
    if flow > 0:
        assert Fraction(actual_units) > Fraction(units)
