"""Algebraic, evidence-conditional Capital portfolio decision primitives.

No policy magic drawdown percentage, leverage cap, financing rate, or
risk-aversion default is defined here. All economic inputs come from caller
or trusted external owners. This is a read-only research capability, not
broker execution, accounting, or market-price admission.

Two separate contracts:
(1) exact one-risky-asset CRRA/Merton diffusion interior solution,
    assuming constant coefficients, frictionless rebalancing and no wealth
    contributions within the continuous-time model;
(2) finite-scenario, one-period concave CRRA utility optimization with
    proportional trading cost and long-only broker initial/maintenance
    constraints. SciPy is the numerical owner, not a formal proof engine.

Neither contract alone solves the whole multi-period problem with
future periodic 1r contributions. That problem is specified by a Bellman
equation in the companion docs and requires a transition/distribution owner.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


class AlgebraicPolicyError(ValueError):
    """Provided economic inputs are infeasible or not well-defined."""


@dataclass(frozen=True)
class Scenario:
    probability: float
    risky_gross_returns: tuple[float, ...]
    cash_gross_return: float
    debt_gross_return: float
    maintenance: tuple[float, ...]


@dataclass(frozen=True)
class OnePeriodProblem:
    """All economic inputs are mandatory; no invented numeric portfolio policy.

    initial_margin[i] = broker cash-equity requirement per unit gross risky
    exposure. A scenario's maintenance requirement is likewise per asset.
    turnover_cost[i] = proportional cost per traded risky dollar.
    old_weights are exposure / before-trade positive account equity.
    The initial normalized equity is exactly 1r, not an inferred account.
    """

    gamma: float
    initial_margin: tuple[float, ...]
    turnover_cost: tuple[float, ...]
    old_weights: tuple[float, ...]
    scenarios: tuple[Scenario, ...]


@dataclass(frozen=True)
class OnePeriodSolution:
    risky_weights: tuple[float, ...]
    cash_weight: float
    debt_weight: float
    transaction_cost: float
    post_trade_equity: float
    scenario_equities: tuple[float, ...]
    expected_equity: float
    expected_utility: float
    certainty_equivalent: float
    numerical_residual: float
    standing: str = "SCENARIO_OPTIMUM_NOT_FORWARD_VERIFIED"


def merton_single_risky_crra(
    *, expected_return: float, cash_rate: float,
    borrowing_rate: float, variance: float, gamma: float
) -> float:
    """Merton CRRA interior fraction with a cash/borrowing-rate kink.

    The risk aversion gamma, conditional expected drift, diffusion variance,
    rates, and *no constraint* are caller/model-owned. No invented leverage
    constant or backtest-derived empirical floor is inserted.
    """
    if not all(math.isfinite(x) for x in (
        expected_return, cash_rate, borrowing_rate, variance, gamma,
    )):
        raise AlgebraicPolicyError("finite diffusion coefficients required")
    if not (gamma > 0 and variance > 0 and borrowing_rate >= cash_rate):
        raise AlgebraicPolicyError("gamma/variance positive and borrow >= lend required")
    lending_opt = (expected_return - cash_rate) / (gamma * variance)
    borrowing_opt = (expected_return - borrowing_rate) / (gamma * variance)
    if lending_opt <= 1:
        return max(0.0, lending_opt)
    if borrowing_opt >= 1:
        return borrowing_opt
    return 1.0


def _validate(problem: OnePeriodProblem) -> None:
    n = len(problem.initial_margin)
    if n == 0 or len(problem.turnover_cost) != n or len(problem.old_weights) != n:
        raise AlgebraicPolicyError("nonempty, aligned asset vector required")
    if not math.isfinite(problem.gamma) or problem.gamma <= 0:
        raise AlgebraicPolicyError("positive finite CRRA gamma required")
    for margin in problem.initial_margin:
        if not math.isfinite(margin) or not 0 < margin <= 1:
            raise AlgebraicPolicyError("broker initial margin must be in (0,1]")
    if any(not math.isfinite(x) or x < 0 for x in problem.turnover_cost):
        raise AlgebraicPolicyError("nonnegative turnover costs required")
    if any(not math.isfinite(x) or x < 0 for x in problem.old_weights):
        raise AlgebraicPolicyError("long-only existing risky weights required")
    if not problem.scenarios:
        raise AlgebraicPolicyError("conditional outcome distribution required")
    probability_sum = 0.0
    for s in problem.scenarios:
        if not (
            math.isfinite(s.probability)
            and s.probability > 0
            and len(s.risky_gross_returns) == n
            and len(s.maintenance) == n
            and math.isfinite(s.cash_gross_return)
            and math.isfinite(s.debt_gross_return)
            and s.cash_gross_return > 0
            and s.debt_gross_return >= s.cash_gross_return
        ):
            raise AlgebraicPolicyError("scenario probability/shape/financing invalid")
        probability_sum += s.probability
        if any(not math.isfinite(x) or x < 0 for x in s.risky_gross_returns):
            raise AlgebraicPolicyError("nonnegative finite risky gross returns required")
        if any(not math.isfinite(x) or not 0 <= x <= 1 for x in s.maintenance):
            raise AlgebraicPolicyError("invalid provider maintenance requirement")
    if not math.isclose(probability_sum, 1.0, rel_tol=1e-10, abs_tol=1e-12):
        raise AlgebraicPolicyError("scenario probabilities must sum to one")


def unitize_external_contribution(
    *, unit_nav_before: float, outstanding_units: float, contribution_r: float
) -> tuple[float, float]:
    """Time-weighted valuation unitization; external inflow changes units only.

    Existing account value = unit_nav_before * outstanding_units.
    New investment unit count = contribution_r / unit_nav_before.
    The identical unit NAV after contribution is mathematically invariant.
    """
    if not all(math.isfinite(x) for x in (
        unit_nav_before, outstanding_units, contribution_r,
    )):
        raise AlgebraicPolicyError("finite equity and capital flow required")
    if unit_nav_before <= 0 or outstanding_units < 0 or contribution_r < 0:
        raise AlgebraicPolicyError("invalid unit NAV or negative contribution")
    new_units = outstanding_units + contribution_r / unit_nav_before
    return unit_nav_before, new_units


def solve_one_period(problem: OnePeriodProblem) -> OnePeriodSolution:
    """Maximize exact expected CRRA utility under linear broker constraints.

    This is a finite-scenario conditional convex optimization problem
    (minimize negative concave utility). SciPy HiGHS/SLSQP are numerical
    methods; result carries residual not proof of optimality, and historical
    sample probabilities are not authenticated conditional forecasts.

    x = (risky positions w[0:n], cash c, debt b, turnover t[0:n]).
    Budget: sum(w)+c-b+sum(k_i*t_i)=1r.
    Turnover: t_i >= |w_i - old_i|.
    Initial margin: sum(m0_i*w_i)+sum(k_i*t_i) <=1r.
    Scenario maintenance: gross equity minus broker requirement >=0:
      sum_i w_i*G_i + c*G_l - b*G_b - sum_i m_i*w_i*G_i >=0.
    """
    _validate(problem)
    # Reuse the established numerical solvers, not a local optimization engine.
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, linprog, minimize

    n = len(problem.initial_margin)
    k = np.asarray(problem.turnover_cost, dtype=float)
    old = np.asarray(problem.old_weights, dtype=float)
    m0 = np.asarray(problem.initial_margin, dtype=float)
    length = 2 * n + 2
    ci, bi, ti = n, n + 1, n + 2
    budget = np.zeros(length)
    budget[:n] = 1.0
    budget[ci] = 1.0
    budget[bi] = -1.0
    budget[ti:] = k

    inequalities: list[Any] = []
    upper: list[float] = []

    initial = np.zeros(length)
    initial[:n] = m0
    initial[ti:] = k
    inequalities.append(initial)
    upper.append(1.0)

    for i in range(n):
        # abs(turnover): w_i - t_i <= old_i
        a = np.zeros(length)
        a[i] = 1.0
        a[ti + i] = -1.0
        inequalities.append(a)
        upper.append(old[i])
        # abs(turnover): -w_i - t_i <= -old_i
        a = np.zeros(length)
        a[i] = -1.0
        a[ti + i] = -1.0
        inequalities.append(a)
        upper.append(-old[i])

    wealth_rows = []
    weights = []
    for s in problem.scenarios:
        asset = np.asarray(s.risky_gross_returns, dtype=float)
        maintain = np.asarray(s.maintenance, dtype=float)
        row = np.zeros(length)
        row[:n] = asset
        row[ci] = s.cash_gross_return
        row[bi] = -s.debt_gross_return
        wealth_rows.append(row)
        weights.append(s.probability)
        # Per scenario maintenance requirement cannot exceed equity.
        a = np.zeros(length)
        a[:n] = asset * (maintain - 1.0)
        a[ci] = -s.cash_gross_return
        a[bi] = s.debt_gross_return
        inequalities.append(a)
        upper.append(0.0)

    A = np.vstack(inequalities)
    bounds = Bounds(np.zeros(length), np.full(length, np.inf))
    # True positive wealth is the mathematical CRRA domain; use the smallest
    # machine-scale positive interior only as a NUMERICAL evaluation guard,
    # never as an investor-selected "bankruptcy safety buffer".
    wealth_matrix = np.vstack(wealth_rows)
    numerical_interior = np.finfo(float).eps
    structural = [
        LinearConstraint(budget, 1.0, 1.0),
        LinearConstraint(A, -np.inf, np.asarray(upper)),
        LinearConstraint(wealth_matrix, numerical_interior, np.inf),
    ]
    # Begin from all-cash when liquidation of old exposure is affordable.
    # This point is strictly positive in every scenario, avoiding evaluating
    # CRRA at a degenerate LP boundary with zero terminal wealth.
    liquidation_cost = float(k @ old)
    if liquidation_cost < 1.0:
        x0 = np.zeros(length)
        x0[ci] = 1.0 - liquidation_cost
        x0[ti:] = old
    else:
        # If immediate liquidation is unaffordable, use HiGHS to maximize
        # the smallest scenario wealth among ALL broker-feasible portfolios.
        # This is a feasibility interior search, not an investment optimizer.
        zobjective = np.zeros(length + 1)
        zobjective[-1] = -1.0
        A_extended = np.hstack((A, np.zeros((A.shape[0], 1))))
        worst_wealth = np.hstack(
            (-wealth_matrix, np.ones((wealth_matrix.shape[0], 1)))
        )
        feasibility = linprog(
            c=zobjective,
            A_ub=np.vstack((A_extended, worst_wealth)),
            b_ub=np.concatenate((np.asarray(upper), np.zeros(len(weights)))),
            A_eq=np.concatenate((budget, [0.0])).reshape(1, -1),
            b_eq=np.asarray([1.0]),
            bounds=[(0, None)] * (length + 1),
            method="highs",
        )
        if not feasibility.success or feasibility.x[-1] <= 0:
            raise AlgebraicPolicyError(
                "no strictly positive-wealth broker-feasible portfolio"
            )
        x0 = np.asarray(feasibility.x[:-1])

    ps = np.asarray(weights, dtype=float)
    gamma = problem.gamma

    def objective(x: Any) -> float:
        W = wealth_matrix @ x
        if np.any(W <= 0):
            return float("inf")
        if gamma == 1:
            return -float(np.dot(ps, np.log(W)))
        return -float(np.dot(ps, np.expm1((1 - gamma) * np.log(W)) / (1 - gamma)))

    def jac(x: Any) -> Any:
        W = wealth_matrix @ x
        if np.any(W <= 0):
            return np.full(length, float("nan"))
        return -wealth_matrix.T @ (ps * W ** (-gamma))

    result = minimize(
        objective, x0, method="SLSQP", jac=jac,
        bounds=bounds, constraints=structural,
        options={"ftol": 1e-11, "maxiter": 2000},
    )
    x = np.asarray(result.x)
    residual = max(
        abs(float(budget @ x - 1)),
        max(0.0, float(np.max(A @ x - np.asarray(upper)))),
        max(0.0, float(-np.min(x))),
        max(0.0, numerical_interior - float(np.min(wealth_matrix @ x))),
    )
    if (not result.success) or residual > 1e-7:
        raise AlgebraicPolicyError(
            f"numerical solver did not certify feasibility: {result.message}; residual={residual}"
        )
    scenario_equities = wealth_matrix @ x
    utility = -objective(x)
    if gamma == 1:
        certainty_equivalent = math.exp(utility)
    else:
        certainty_equivalent = math.exp(
            math.log1p((1 - gamma) * utility) / (1 - gamma)
        )
    fees = float(k @ x[ti:])
    return OnePeriodSolution(
        risky_weights=tuple(float(v) for v in x[:n]),
        cash_weight=float(x[ci]),
        debt_weight=float(x[bi]),
        transaction_cost=fees,
        post_trade_equity=1.0 - fees,
        scenario_equities=tuple(float(v) for v in scenario_equities),
        expected_equity=float(ps @ scenario_equities),
        expected_utility=float(utility),
        certainty_equivalent=certainty_equivalent,
        numerical_residual=residual,
    )
