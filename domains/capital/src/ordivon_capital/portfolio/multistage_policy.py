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
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from ordivon_capital.portfolio.algebraic_policy import AlgebraicPolicyError


@dataclass(frozen=True)
class InformationNode:
    """One history node with edge facts observed on arrival from parent.

    root: no parent, t=0, conditional_prob=1, no incoming gross/maintenance.
    decision node: current initial_margin and turnover_cost are required.
    terminal node: no initial_margin / turnover_cost, no trade or deposit.

    Parent->child gross returns are each relative to its parent's decision
    moment, and observed_label may represent a separately observable signal.
    Identical siblings with identical observable inputs cannot be distinguished
    by a legal policy and are rejected rather than granting hidden foresight.
    """

    id: str
    parent: str | None
    t: int
    conditional_probability: float
    risky_gross: tuple[float, ...] = ()
    cash_gross: float = 1.0
    debt_gross: float = 1.0
    maintenance: tuple[float, ...] = ()
    initial_margin: tuple[float, ...] = ()
    turnover_cost: tuple[float, ...] = ()
    terminal: bool = False
    observed_label: str = ""


@dataclass(frozen=True)
class MultistageProblem:
    gamma: float
    nodes: tuple[InformationNode, ...]
    # If specified, every terminal observation has a caller-owned cash
    # obligation, measured in the same 1r unit as the investment account.
    # These obligations are deducted from *terminal consumption utility*,
    # not silently represented as broker collateral or early cash deposits.
    terminal_liabilities_r: dict[str, float] | None = None
    # Economic payment due AFTER the explicitly timed monthly 1r deposit
    # and BEFORE the rebalance. Earlier due dates are outside this contract.
    node_outflow_after_contribution_r: dict[str, float] | None = None


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


@dataclass(frozen=True)
class _ValidTree:
    ordered: tuple[InformationNode, ...]
    decision: tuple[InformationNode, ...]
    leaves: tuple[InformationNode, ...]
    by_id: dict[str, InformationNode]
    probability: dict[str, float]
    asset_count: int
    months: int


def _finite(x: float) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x)


def _validate_tree(problem: MultistageProblem) -> _ValidTree:
    if not _finite(problem.gamma) or problem.gamma <= 0:
        raise AlgebraicPolicyError("positive CRRA risk aversion required")
    nodes = problem.nodes
    if not nodes or not all(isinstance(n, InformationNode) for n in nodes):
        raise AlgebraicPolicyError("nonempty information tree required")
    by_id = {n.id: n for n in nodes}
    if len(by_id) != len(nodes) or any(not n.id or not isinstance(n.id, str) for n in nodes):
        raise AlgebraicPolicyError("unique nonblank observation identifiers required")
    roots = [n for n in nodes if n.parent is None]
    if len(roots) != 1 or roots[0].terminal or roots[0].t != 0:
        raise AlgebraicPolicyError("one nonterminal time-zero root required")
    root = roots[0]
    n_assets = len(root.initial_margin)
    if n_assets <= 0:
        raise AlgebraicPolicyError("nonempty risky universe required")
    if not (
        root.conditional_probability == 1.0
        and root.risky_gross == ()
        and root.maintenance == ()
        and root.cash_gross == root.debt_gross == 1.0
    ):
        raise AlgebraicPolicyError("root has no incoming market return")
    ordered = tuple(sorted(nodes, key=lambda x: (x.t, x.id)))
    children: dict[str, list[InformationNode]] = defaultdict(list)
    for node in ordered:
        if not isinstance(node.t, int) or node.t < 0:
            raise AlgebraicPolicyError("nonnegative integer month index required")
        if not _finite(node.conditional_probability) or node.conditional_probability <= 0:
            raise AlgebraicPolicyError("strictly positive conditional probability required")
        if node.parent is not None:
            if node.parent not in by_id:
                raise AlgebraicPolicyError("unrecognized parent")
            parent = by_id[node.parent]
            if parent.terminal or node.t != parent.t + 1:
                raise AlgebraicPolicyError("invalid parent state or skipped monthly decision")
            if node.observed_label is None or not isinstance(node.observed_label, str):
                raise AlgebraicPolicyError("unobservable branch label")
            if not (
                len(node.risky_gross) == len(node.maintenance) == n_assets
                and all(_finite(x) and x >= 0 for x in node.risky_gross)
                and all(_finite(x) and 0 <= x <= 1 for x in node.maintenance)
                and _finite(node.cash_gross)
                and _finite(node.debt_gross)
                and node.cash_gross > 0
                and node.debt_gross >= node.cash_gross
            ):
                raise AlgebraicPolicyError("invalid observed return or margin contract")
            children[node.parent].append(node)
        if node.terminal:
            if node.initial_margin or node.turnover_cost:
                raise AlgebraicPolicyError("terminal nodes cannot trade")
        elif not (
            len(node.initial_margin) == len(node.turnover_cost) == n_assets
            and all(_finite(x) and 0 < x <= 1 for x in node.initial_margin)
            and all(_finite(x) and x >= 0 for x in node.turnover_cost)
        ):
            raise AlgebraicPolicyError("decision node requires provider margin and costs")
    for parent in ordered:
        if parent.terminal:
            if parent.id in children:
                raise AlgebraicPolicyError("terminal node cannot have children")
            continue
        branch = children.get(parent.id, [])
        if not branch:
            raise AlgebraicPolicyError("every decision needs observed next-month outcomes")
        if not math.isclose(
            math.fsum(child.conditional_probability for child in branch),
            1.0, rel_tol=1e-10, abs_tol=1e-12,
        ):
            raise AlgebraicPolicyError("branch conditional probabilities must sum to one")
        seen: set[tuple[Any, ...]] = set()
        for child in branch:
            signature = (
                child.risky_gross, child.cash_gross, child.debt_gross,
                child.maintenance, child.observed_label,
            )
            if signature in seen:
                raise AlgebraicPolicyError(
                    "indistinguishable observed branches grant hidden future information"
                )
            seen.add(signature)

    leaves = tuple(n for n in ordered if n.terminal)
    if not leaves:
        raise AlgebraicPolicyError("at least one finite terminal state required")
    if problem.node_outflow_after_contribution_r is not None:
        claims = problem.node_outflow_after_contribution_r
        decision_ids = {n.id for n in ordered if not n.terminal}
        if not isinstance(claims, dict) or set(claims) != decision_ids:
            raise AlgebraicPolicyError(
                "intermediate obligations require exact decision-node coverage"
            )
        if any(
            not _finite(v) or isinstance(v, bool) or v < 0
            for v in claims.values()
        ):
            raise AlgebraicPolicyError(
                "nonnegative finite decision-date obligations required"
            )
    if problem.terminal_liabilities_r is not None:
        claims = problem.terminal_liabilities_r
        if not isinstance(claims, dict) or set(claims) != {n.id for n in leaves}:
            raise AlgebraicPolicyError(
                "terminal liabilities require one explicit obligation per leaf"
            )
        if any(
            not _finite(v) or isinstance(v, bool) or v < 0
            for v in claims.values()
        ):
            raise AlgebraicPolicyError("nonnegative finite terminal liabilities required")
    depths = {n.t for n in leaves}
    if len(depths) != 1:
        raise AlgebraicPolicyError("all paths must have the same contribution horizon")
    months = depths.pop()
    if months < 1:
        raise AlgebraicPolicyError("at least one month of risk transition required")
    if any(n.t >= months for n in ordered if not n.terminal):
        raise AlgebraicPolicyError("no trading on or after terminal date")
    probability: dict[str, float] = {}
    for node in ordered:
        if node.parent is None:
            probability[node.id] = 1.0
        else:
            probability[node.id] = (
                probability[node.parent] * node.conditional_probability
            )
    if not math.isclose(
        math.fsum(probability[n.id] for n in leaves),
        1.0, rel_tol=1e-10, abs_tol=1e-12,
    ):
        raise AlgebraicPolicyError("terminal event probability must be one")
    return _ValidTree(
        ordered, tuple(n for n in ordered if not n.terminal),
        leaves, by_id, probability, n_assets, months,
    )


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
      pretrade_equity_edge > 0 before any 1r rescue deposit
    Terminal expected CRRA utility is strictly concave in positive wealth.
    """
    tree = _validate_tree(problem)
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, linprog, minimize

    n = tree.asset_count
    decisions = tree.decision
    width = 2 * n + 2
    size = len(decisions) * width
    offsets = {node.id: idx * width for idx, node in enumerate(decisions)}
    cost_start = n + 2
    rhs_eq: list[float] = []
    eq_rows: list[Any] = []
    ub_rows: list[Any] = []
    ub_rhs: list[float] = []
    prewealth_rows: list[Any] = []
    terminal_rows: list[Any] = []
    terminal_probs: list[float] = []
    all_wealth_rows: dict[str, Any] = {}

    def prewealth(node: InformationNode) -> Any:
        """Linear pre-deposit value after the parent->child market transition."""
        row = np.zeros(size, dtype=float)
        if node.parent is None:
            return row
        parent = offsets[node.parent]
        row[parent:parent + n] = np.asarray(node.risky_gross)
        row[parent + n] = node.cash_gross
        row[parent + n + 1] = -node.debt_gross
        return row

    for node in tree.ordered:
        if node.parent is not None:
            incoming = prewealth(node)
            all_wealth_rows[node.id] = incoming
            prewealth_rows.append(incoming)
            # Parent-edge maintenance must be met before next 1r deposit.
            margin = np.zeros(size, dtype=float)
            p = offsets[node.parent]
            margin[p:p + n] = (
                (np.asarray(node.maintenance) - 1.0)
                * np.asarray(node.risky_gross)
            )
            margin[p + n] = -node.cash_gross
            margin[p + n + 1] = node.debt_gross
            ub_rows.append(margin)
            ub_rhs.append(0.0)
        if node.terminal:
            terminal_rows.append(all_wealth_rows[node.id])
            terminal_probs.append(tree.probability[node.id])
            continue

        index = offsets[node.id]
        row = np.zeros(size)
        row[index:index + n] = 1.0
        row[index + n] = 1.0
        row[index + n + 1] = -1.0
        row[index + cost_start:index + cost_start + n] = node.turnover_cost
        if node.parent is not None:
            row -= all_wealth_rows[node.id]
        eq_rows.append(row)
        due = (
            0.0 if problem.node_outflow_after_contribution_r is None
            else problem.node_outflow_after_contribution_r[node.id]
        )
        rhs_eq.append(1.0 - due)  # Actual monthly 1r minus paid cash outflow.

        # Linear epigraph for each turnover absolute value.
        for i in range(n):
            old = np.zeros(size)
            if node.parent is not None:
                old[offsets[node.parent] + i] = node.risky_gross[i]
            buy = np.zeros(size)
            buy[index + i] = 1.0
            buy[index + cost_start + i] = -1.0
            buy -= old
            ub_rows.append(buy)
            ub_rhs.append(0.0)

            sell = np.zeros(size)
            sell[index + i] = -1.0
            sell[index + cost_start + i] = -1.0
            sell += old
            ub_rows.append(sell)
            ub_rhs.append(0.0)

        initial_margin = np.zeros(size)
        initial_margin[index:index + n] = (
            np.asarray(node.initial_margin) - 1.0
        )
        initial_margin[index + n] = -1.0
        initial_margin[index + n + 1] = 1.0
        ub_rows.append(initial_margin)
        ub_rhs.append(0.0)

    A_eq = np.vstack(eq_rows)
    b_eq = np.asarray(rhs_eq)
    A_ub = np.vstack(ub_rows)
    b_ub = np.asarray(ub_rhs)
    W_leaf = np.vstack(terminal_rows)
    W_arrival = np.vstack(prewealth_rows)
    liabilities = np.asarray(
        [
            0.0 if problem.terminal_liabilities_r is None
            else problem.terminal_liabilities_r[leaf.id]
            for leaf in tree.leaves
        ],
        dtype=float,
    )
    leaf_probabilities = np.asarray(terminal_probs)
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
        and float(np.min(W_arrival @ x0)) > numerical_interior
        and float(np.min(W_leaf @ x0 - liabilities)) > numerical_interior
    )
    if not all_cash_feasible:
        # A cash-only investment is insufficient to pay all obligations.
        # Use the existing mature HiGHS LP to maximize the smallest
        # state-wise terminal surplus. Do not fake a default risk budget.
        # If no positive surplus exists, the requested CRRA objective has
        # no feasible solution under these actual contract assumptions.
        ext = np.zeros((A_ub.shape[0], 1))
        arrival = np.hstack((-W_arrival, np.ones((W_arrival.shape[0], 1))))
        disposable = np.hstack((-W_leaf, np.ones((W_leaf.shape[0], 1))))
        c = np.zeros(size + 1)
        c[-1] = -1.0
        lp = linprog(
            c,
            A_ub=np.vstack((np.hstack((A_ub, ext)), arrival, disposable)),
            b_ub=np.concatenate((
                b_ub,
                np.zeros(W_arrival.shape[0]),
                -liabilities,
            )),
            A_eq=np.hstack((A_eq, np.zeros((A_eq.shape[0], 1)))),
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

    constraints = [
        LinearConstraint(A_eq, b_eq, b_eq),
        LinearConstraint(A_ub, -np.inf, b_ub),
        LinearConstraint(W_arrival, numerical_interior, np.inf),
        LinearConstraint(W_leaf, liabilities + numerical_interior, np.inf),
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

    def neg_objective(x: Any) -> float:
        value, _ = utility_and_gradient(x)
        return -value

    def neg_gradient(x: Any) -> Any:
        _, grad = utility_and_gradient(x)
        return -grad

    found = minimize(
        neg_objective, x0, method="SLSQP", jac=neg_gradient,
        bounds=bounds, constraints=constraints,
        options={"ftol": 1e-11, "maxiter": 3000},
    )
    x = np.asarray(found.x, dtype=float)
    equality_error = float(np.max(np.abs(A_eq @ x - b_eq)))
    inequality_error = float(max(
        0.0,
        np.max(A_ub @ x - b_ub),
        -np.min(x),
        numerical_interior - np.min(W_arrival @ x),
        np.max(liabilities + numerical_interior - W_leaf @ x),
    ))
    if (
        not found.success
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
    certificate = linprog(
        -gradient,
        A_ub=np.vstack((A_ub, -W_arrival, -W_leaf)),
        b_ub=np.concatenate((
            b_ub,
            -np.full(W_arrival.shape[0], numerical_interior),
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
    gap = max(0.0, float(gradient @ (certificate.x - x)))
    if not math.isfinite(gap):
        raise AlgebraicPolicyError("nonfinite upper optimality bound")
    # Gap is a visible numerical evidence value, never turned into a
    # fictitious mathematical or portfolio-risk guarantee.
    terminal_wealth = W_leaf @ x
    disposable_wealth = terminal_wealth - liabilities
    # Preserve existing gross-account CE semantics even if the objective
    # explicitly uses disposable surplus. Renaming fields by interpretation
    # would silently corrupt old read-only consumers.
    if gamma == 1:
        certainty_equivalent_disposable = math.exp(value)
        certainty_equivalent_gross = math.exp(
            float(leaf_probabilities @ np.log(terminal_wealth))
        )
    else:
        disposable_moment = float(
            leaf_probabilities @ disposable_wealth ** (1 - gamma)
        )
        gross_moment = float(
            leaf_probabilities @ terminal_wealth ** (1 - gamma)
        )
        certainty_equivalent_disposable = math.exp(
            math.log(disposable_moment) / (1 - gamma)
        )
        certainty_equivalent_gross = math.exp(
            math.log(gross_moment) / (1 - gamma)
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

    parser = argparse.ArgumentParser(
        description="Read-only finite-scenario 1r CRRA multi-period research"
    )
    parser.add_argument("--input", type=str, default="-")
    args = parser.parse_args()
    try:
        if args.input == "-":
            payload = json.load(sys.stdin)
        else:
            from pathlib import Path as _Path

            with _Path(args.input).open(encoding="utf-8") as f:
                payload = json.load(f)
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
                "expected only gamma and nodes (optional terminal_liabilities_r)"
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
