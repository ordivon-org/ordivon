"""Finite-scenario multistage CRRA investment with one 1r monthly contribution.

This is a pure, read-only Capital Portfolio research binding to the existing
SciPy HiGHS and SLSQP solvers. No market probabilities, loan prices, margin
limits, stochastic states, leverage ceilings or investor utility are invented.
All branches, observable information and economic contracts are supplied.

A tree node is a *publicly distinguishable observation history*, not a
foresight-labelled future. One trade decision exists per information node;
the path cannot branch into independent decisions before uncertainty arrives.

A decision node t receives exactly one 1r deposit after the preceding
edge's margin check. Terminal nodes receive no new money and cannot trade.
Consequently "terminalR" is account value after T contributions, whereas
the TWR unit account requires separate unitization.

Finite scenario expected CRRA utility of net terminal liabilities plus linear self-financing/trade/margin
constraints is a concave maximization on a convex feasible set. A supporting
hyperplane LP gives a *numerical global optimality-gap upper bound*, not
a formal proof of SciPy or an authenticated return forecast.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from ordivon_capital.portfolio.constraint_compiler import compile_multistage_constraints
from ordivon_capital.portfolio.crra_numeric import certainty_equivalent
from ordivon_capital.portfolio.information_tree import (
    InformationNode,
    MultistageProblem,
    validate_information_tree,
)
from ordivon_capital.portfolio.policy_contract import AlgebraicPolicyError

# The existing PIT source consumer exercises this exact validation contract
# through the old module import. Re-export the same function, not its logic.
_validate_tree = validate_information_tree


@dataclass(frozen=True)
class MultistageSolution:
    contributions_r_per_path: int
    expected_terminal_r: float
    certainty_equivalent_terminal_r: float
    expected_utility: float
    expected_disposable_terminal_r: float
    # Independent from gross-account CE: respects terminal obligations,
    # while the original field remains the gross terminal equity CE.
    certainty_equivalent_disposable_r: float
    root_risky_r: tuple[float, ...]
    root_cash_r: float
    root_debt_r: float
    node_decisions_r: dict[str, dict[str, Any]]
    terminal_distribution: dict[str, dict[str, float]]
    equality_residual: float
    inequality_residual: float
    concavity_global_utility_gap_upper: float
    standing: str = "FINITE_TREE_CONDITIONAL_NUMERIC_NOT_MARKET_VERIFIED"


def solve_multistage(problem: MultistageProblem) -> MultistageSolution:
    """Solve a scenario-tree convex program without market/broker side effects.

    Every decision node t has a deterministic exogenous 1r contribution.
    Parent-edge maintenance is checked BEFORE that contribution is accepted.
    Distinct paths cannot choose distinct decisions prior to their branching.

    For n risk assets decision y=(a_1..a_n,c,b,h_1..h_n).
      sum(a)+c-b+cost.h = 1r+pretrade_equity
      h_i >= abs(a_i - pretrade_risky_i)
      initial_margin(a) <= post_trade_equity
      pretrade_equity_edge >= maintenance_edge(risky_gross)
      pretrade_equity_edge >= 0 before any 1r rescue deposit
    Terminal expected CRRA utility is strictly concave in positive wealth.
    """
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, linprog, minimize
    from scipy.sparse import csr_matrix, hstack, vstack

    compiled = compile_multistage_constraints(problem)
    tree = compiled.tree
    n = tree.asset_count
    decisions = tree.decision
    offsets, size = compiled.offsets, compiled.size
    cost_start = n + 2
    A_eq, b_eq = compiled.A_eq, compiled.b_eq
    A_ub, b_ub = compiled.A_ub, compiled.b_ub
    W_leaf, W_arrival = compiled.W_leaf, compiled.W_arrival
    liabilities, leaf_probabilities = compiled.liabilities, compiled.probabilities
    numerical_interior = float(np.finfo(float).eps)

    # An all-cash policy is a constructive, no-credit, positive-wealth
    # feasible point. It respects exact contribution and all collateral
    # constraints without inventing "safe" leverage or a fallback trade.
    x0 = np.zeros(size, dtype=float)
    for node in decisions:
        index = offsets[node.id]
        due = (
            0.0 if problem.node_outflow_after_contribution_r is None
            else problem.node_outflow_after_contribution_r[node.id]
        )
        x0[index + n] = 1.0 - due + (
            0.0 if node.parent is None
            else node.cash_gross * x0[offsets[node.parent] + n]
        )
    # Check the constructed feasible point; invalid consumer constraints
    # cannot be "repaired" by silently loosening provider margins.
    all_cash_feasible = (
        float(np.min(x0)) >= 0.0
        and float(np.max(np.abs(A_eq @ x0 - b_eq))) <= 1e-9
        and float(np.max(A_ub @ x0 - b_ub)) <= 1e-9
        and float(np.min(W_arrival @ x0)) >= 0.0
        and float(np.min(W_leaf @ x0 - liabilities)) > numerical_interior
    )
    if not all_cash_feasible:
        # A cash-only investment is insufficient to pay all obligations.
        # Use the existing mature HiGHS LP to maximize the smallest
        # state-wise terminal surplus. Do not fake a default risk budget.
        # If no positive surplus exists, the requested CRRA objective has
        # no feasible solution under these actual contract assumptions.
        ext = csr_matrix((A_ub.shape[0], 1))
        # Zero equity without a loan is solvent before next month's 1r.
        # The strictly positive CRRA domain applies only to terminal surplus.
        arrival = hstack((-W_arrival, csr_matrix((W_arrival.shape[0], 1))), format='csr')
        disposable = hstack((-W_leaf, csr_matrix(np.ones((W_leaf.shape[0], 1)))), format='csr')
        c = np.zeros(size + 1)
        c[-1] = -1.0
        lp = linprog(
            c,
            A_ub=vstack((hstack((A_ub, ext)), arrival, disposable), format='csr'),
            b_ub=np.concatenate((
                b_ub,
                np.zeros(W_arrival.shape[0]),
                -liabilities,
            )),
            A_eq=hstack((A_eq, csr_matrix((A_eq.shape[0], 1))), format='csr'),
            b_eq=b_eq,
            bounds=[(0.0, None)] * (size + 1),
            method="highs",
        )
        if not lp.success or lp.x[-1] <= numerical_interior:
            raise AlgebraicPolicyError(
                "no strictly positive post-liability consumption "
                "or funded intermediate obligations under stated contracts"
            )
        x0 = np.asarray(lp.x[:-1], dtype=float)

    # SLSQP is a dense carrier. Convert only at this explicit boundary;
    # feasibility, matrix-vector products and certificate LP remain sparse.
    constraints = [
        LinearConstraint(A_eq.toarray(), b_eq, b_eq),
        LinearConstraint(A_ub.toarray(), -np.inf, b_ub),
        LinearConstraint(W_arrival.toarray(), 0.0, np.inf),
        LinearConstraint(W_leaf.toarray(), liabilities + numerical_interior, np.inf),
    ]
    bounds = Bounds(np.zeros(size), np.full(size, np.inf))
    gamma = problem.gamma

    def utility_and_gradient(x: Any) -> tuple[float, Any]:
        W = W_leaf @ x - liabilities
        if np.any(W <= 0):
            return float("-inf"), np.full(size, float("nan"))
        if gamma == 1:
            utility = float(leaf_probabilities @ np.log(W))
        else:
            utility = float(
                leaf_probabilities @ (
                    np.expm1((1.0 - gamma) * np.log(W)) / (1.0 - gamma)
                )
            )
        grad = W_leaf.T @ (leaf_probabilities * W ** (-gamma))
        return utility, grad

    # SciPy's jac=True contract caches the joint objective/gradient at the
    # current point. Both use the same terminal wealth matrix product; separate
    # callbacks would recompute the full pair at the same trial point.
    def neg_objective_and_gradient(x: Any) -> tuple[float, Any]:
        value, grad = utility_and_gradient(x)
        return -value, -grad

    found = minimize(
        neg_objective_and_gradient, x0, method="SLSQP", jac=True,
        bounds=bounds, constraints=constraints,
        options={"ftol": 1e-11, "maxiter": 3000},
    )
    x = np.asarray(found.x, dtype=float)
    equality_error = float(np.max(np.abs(A_eq @ x - b_eq)))
    inequality_error = float(max(
        0.0,
        np.max(A_ub @ x - b_ub),
        -np.min(x),
        -np.min(W_arrival @ x),
        np.max(liabilities + numerical_interior - W_leaf @ x),
    ))
    if (
        not found.success
        or not np.all(np.isfinite(x))
        or not math.isfinite(equality_error)
        or not math.isfinite(inequality_error)
        or equality_error > 1e-7
        or inequality_error > 1e-7
    ):
        raise AlgebraicPolicyError(
            "multistage numerical optimization did not yield a feasible "
            f"candidate: {found.message}; equality={equality_error}; "
            f"inequality={inequality_error}"
        )

    # Finite-scenario CRRA objective is concave on the positive-wealth domain.
    # Its tangent at a feasible point is an affine GLOBAL upper bound.
    # Maximize that tangent over the *same primal feasible polyhedron*
    # using proven upstream HiGHS linear programming.
    value, gradient = utility_and_gradient(x)
    if not math.isfinite(value) or not np.all(np.isfinite(gradient)):
        raise AlgebraicPolicyError("nonfinite utility or gradient at solver candidate")
    certificate = linprog(
        -gradient,
        A_ub=vstack((A_ub, -W_arrival, -W_leaf), format='csr'),
        b_ub=np.concatenate((
            b_ub,
            np.zeros(W_arrival.shape[0]),
            -liabilities - numerical_interior,
        )),
        A_eq=A_eq, b_eq=b_eq,
        bounds=[(0.0, None)] * size, method="highs",
    )
    if not certificate.success:
        raise AlgebraicPolicyError(
            "independent LP supporting-hyperplane bound unavailable: "
            + certificate.message
        )
    raw_gap = float(gradient @ (certificate.x - x))
    if not math.isfinite(raw_gap):
        raise AlgebraicPolicyError("nonfinite upper optimality bound")
    gap = max(0.0, raw_gap)
    # Gap is a visible numerical evidence value, never turned into a
    # fictitious mathematical or portfolio-risk guarantee.
    terminal_wealth = W_leaf @ x
    disposable_wealth = terminal_wealth - liabilities
    # Preserve existing gross-account CE semantics even if the objective
    # explicitly uses disposable surplus. Renaming fields by interpretation
    # would silently corrupt old read-only consumers.
    certainty_equivalent_disposable = certainty_equivalent(
        disposable_wealth, leaf_probabilities, gamma
    )
    certainty_equivalent_gross = certainty_equivalent(
        terminal_wealth, leaf_probabilities, gamma
    )
    output_decisions: dict[str, dict[str, Any]] = {}
    for node in decisions:
        start = offsets[node.id]
        pos = x[start:start + n]
        cash, debt = x[start + n:start + n + 2]
        fees = float(
            np.asarray(node.turnover_cost)
            @ x[start + cost_start:start + cost_start + n]
        )
        after_trade = float(np.sum(pos) + cash - debt)
        output_decisions[node.id] = {
            "stage": node.t,
            "historyProbability": tree.probability[node.id],
            "assetExposuresR": tuple(float(v) for v in pos),
            "cashR": float(cash),
            "debtR": float(debt),
            "tradeCostR": fees,
            "postTradeEquityR": after_trade,
            "contributionR": 1.0,
            "outflowAfterContributionR": (
                0.0 if problem.node_outflow_after_contribution_r is None
                else problem.node_outflow_after_contribution_r[node.id]
            ),
        }
    distribution = {
        leaf.id: {
            "probability": tree.probability[leaf.id],
            "terminalR": float(value_r),
            "obligationR": float(obligation),
            "disposableTerminalR": float(value_r - obligation),
        }
        for leaf, value_r, obligation in zip(
            tree.leaves, terminal_wealth, liabilities, strict=True
        )
    }
    first = output_decisions[decisions[0].id]
    return MultistageSolution(
        contributions_r_per_path=tree.months,
        expected_terminal_r=float(leaf_probabilities @ terminal_wealth),
        certainty_equivalent_terminal_r=certainty_equivalent_gross,
        expected_utility=value,
        expected_disposable_terminal_r=float(
            leaf_probabilities @ disposable_wealth
        ),
        certainty_equivalent_disposable_r=certainty_equivalent_disposable,
        root_risky_r=first["assetExposuresR"],
        root_cash_r=first["cashR"],
        root_debt_r=first["debtR"],
        node_decisions_r=output_decisions,
        terminal_distribution=distribution,
        equality_residual=equality_error,
        inequality_residual=inequality_error,
        concavity_global_utility_gap_upper=gap,
    )

def main() -> int:
    """Existing Runtime native Python module consumer, not an execution API.

    JSON shape:
      {"gamma": positive_real, "nodes": [InformationNode field objects...]}
    No return forecasts/borrowing terms or investor gamma are invented.
    """
    import argparse
    import dataclasses
    import json
    import sys

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result = {}
        for key, value in pairs:
            if key in result:
                raise AlgebraicPolicyError(f"duplicate JSON input key: {key}")
            result[key] = value
        return result

    parser = argparse.ArgumentParser(
        description="Read-only finite-scenario 1r CRRA multi-period research"
    )
    parser.add_argument("--input", type=str, default="-")
    args = parser.parse_args()
    try:
        if args.input == "-":
            payload = json.load(sys.stdin, object_pairs_hook=unique_object)
        else:
            from pathlib import Path as _Path

            with _Path(args.input).open(encoding="utf-8") as f:
                payload = json.load(f, object_pairs_hook=unique_object)
        allowed_payload = {
            "gamma", "nodes", "terminal_liabilities_r",
            "node_outflow_after_contribution_r",
        }
        if (
            not isinstance(payload, dict)
            or not {"gamma", "nodes"} <= set(payload)
            or set(payload) - allowed_payload
        ):
            raise AlgebraicPolicyError(
                "expected only gamma and nodes (optional terminal_liabilities_r, "
                "node_outflow_after_contribution_r)"
            )
        if not isinstance(payload["nodes"], list):
            raise AlgebraicPolicyError("nodes must be a JSON list of information sets")
        allowed = set(InformationNode.__dataclass_fields__)
        nodes = []
        for raw in payload["nodes"]:
            if not isinstance(raw, dict) or set(raw) - allowed:
                raise AlgebraicPolicyError("unknown JSON information node fields")
            normalized = dict(raw)
            for key in (
                "risky_gross", "maintenance", "initial_margin", "turnover_cost"
            ):
                if key in normalized:
                    if not isinstance(normalized[key], list):
                        raise AlgebraicPolicyError(f"{key} must be JSON array")
                    normalized[key] = tuple(normalized[key])
            nodes.append(InformationNode(**normalized))
        result = solve_multistage(
            MultistageProblem(
                gamma=payload["gamma"],
                nodes=tuple(nodes),
                terminal_liabilities_r=payload.get("terminal_liabilities_r"),
                node_outflow_after_contribution_r=payload.get(
                    "node_outflow_after_contribution_r"
                ),
            )
        )
    except (ValueError, TypeError, KeyError) as exc:
        parser.error(f"invalid economic research input: {exc}")
    print(
        json.dumps(
            {
                "standing": result.standing,
                "inputStanding": "CALLER_SUPPLIED_NOT_MARKET_ATTESTED",
                "effectStanding": "READ_ONLY_NO_BROKER_NO_PAPER_LEDGER",
                "model": "MULTISTAGE_MONTHLY_ONE_R_CONDITIONAL_CRRA",
                "solution": dataclasses.asdict(result),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
