"""Pure multistage financial information-tree specification and validation.

Represents the observable branching history, conditional probabilities,
per-period financing/margin contracts and dated liabilities. No NumPy,
SciPy, provider connection, accounting effects or optimization is owned here.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from .algebraic_policy import AlgebraicPolicyError


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
class ValidatedInformationTree:
    ordered: tuple[InformationNode, ...]
    decision: tuple[InformationNode, ...]
    leaves: tuple[InformationNode, ...]
    by_id: dict[str, InformationNode]
    probability: dict[str, float]
    asset_count: int
    months: int


def _finite(x: float) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x)


def validate_information_tree(problem: MultistageProblem) -> ValidatedInformationTree:
    """Validate observable histories, contracts and nonanticipativity without a solver.

    Provider values remain caller-supplied: validity here is not market
    publication-time attestation, broker approval, or portfolio optimality.
    """
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
    return ValidatedInformationTree(
        ordered, tuple(n for n in ordered if not n.terminal),
        leaves, by_id, probability, n_assets, months,
    )
