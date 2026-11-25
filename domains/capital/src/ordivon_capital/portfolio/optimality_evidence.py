"""Exact-rational witness and tangent bound, separate from numerical solver.

The exact model interprets supplied finite numbers as rationals and multiplies
conditional probabilities exactly. For a fixed risky policy, minimizing
turnover and cancelling simultaneous cash/debt weakly improves wealth on
every edge (nonnegative fees and borrow >= lend). Inductively this preserves
feasibility and dominates the original utility. Thus the canonical subset
suffices for a global upper bound. No solver status is an exact certificate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from .information_tree import MultistageProblem, validate_information_tree
from .policy_contract import finite_economic_number

Q = Fraction
ZERO = Q(0)
_MAX_EXACT_BITS = 16_384


@dataclass(frozen=True)
class DualProposal:
    inequality_marginals: tuple[float, ...]
    equality_marginals: tuple[float, ...]


@dataclass(frozen=True)
class OptimalityEvidence:
    numerical_tangent_gap_estimate: float
    certified_canonical_gap_upper: float | None
    standing: str
    reason: str
    dual_proposal: DualProposal | None = None


def certify_canonical_gap(
    problem: MultistageProblem,
    risky_policy: dict[str, tuple[float, ...]],
    inequality_multipliers: Any,
    equality_multipliers: Any,
    numerical_estimate: float,
) -> OptimalityEvidence:
    """Bound optimum minus utility of a reconstructed exact feasible policy.

    Supplied multipliers are untrusted proposals, even if numerically optimal.
    Exact residual correction over finite canonical boxes gives weak duality.
    Resource scope limits qualification, never the admitted economic model.
    """

    def unknown(reason: str) -> OptimalityEvidence:
        return OptimalityEvidence(numerical_estimate, None, "UNKNOWN", reason)

    def within_budget(values: Any) -> bool:
        return all(
            max(v.numerator.bit_length(), v.denominator.bit_length()) <= _MAX_EXACT_BITS
            for v in values
        )

    tree = validate_information_tree(problem)
    # Bound exact arithmetic work; general fractional powers need interval
    # derivatives and are deliberately not promoted to certified evidence.
    gamma = int(problem.gamma)
    if gamma != problem.gamma or not 1 <= gamma <= 16:
        return unknown("INTEGER_GAMMA_1_TO_16_ONLY")
    if len(tree.ordered) > 63 or tree.asset_count > 16:
        return unknown("EXACT_WITNESS_RESOURCE_SCOPE")

    n = tree.asset_count
    width = 2 * n + 2
    offsets = {node.id: i * width for i, node in enumerate(tree.decision)}
    size = len(offsets) * width
    if set(risky_policy) != set(offsets):
        return unknown("INEXACT_WITNESS")
    x = [ZERO] * size
    cap = [ZERO] * size
    probabilities: dict[str, Fraction] = {}
    eq: list[tuple[dict[int, Fraction], Fraction]] = []
    ub: list[tuple[dict[int, Fraction], Fraction]] = []
    arrivals: list[dict[int, Fraction]] = []
    leaves: list[tuple[dict[int, Fraction], Fraction, Fraction]] = []

    def dot(row: dict[int, Fraction], vector: list[Fraction]) -> Fraction:
        return sum((a * vector[j] for j, a in row.items()), ZERO)

    for node in tree.ordered:
        incoming: dict[int, Fraction] = {}
        old = [ZERO] * n
        old_cap = [ZERO] * n
        wealth_cap = ZERO
        probabilities[node.id] = Q(node.conditional_probability)
        if node.parent is not None:
            p = offsets[node.parent]
            gross = tuple(map(Q, node.risky_gross))
            lend, borrow = Q(node.cash_gross), Q(node.debt_gross)
            probabilities[node.id] *= probabilities[node.parent]
            incoming = {p + i: g for i, g in enumerate(gross)}
            incoming.update({p + n: lend, p + n + 1: -borrow})
            old = [x[p + i] * g for i, g in enumerate(gross)]
            old_cap = [cap[p + i] * g for i, g in enumerate(gross)]
            wealth_cap = sum(old_cap, ZERO) + cap[p + n] * lend
            margin = {
                p + i: (Q(m) - 1) * g
                for i, (m, g) in enumerate(zip(node.maintenance, gross, strict=True))
            }
            margin.update({p + n: -lend, p + n + 1: borrow})
            ub.append((margin, ZERO))
            arrivals.append(incoming)
            if dot(incoming, x) < 0 or dot(margin, x) > 0:
                return unknown("INEXACT_WITNESS")
        if node.terminal:
            liability = (
                ZERO
                if problem.terminal_liabilities_r is None
                else Q(problem.terminal_liabilities_r[node.id])
            )
            if dot(incoming, x) <= liability:
                return unknown("INEXACT_WITNESS")
            leaves.append((incoming, liability, probabilities[node.id]))
            continue
        j = offsets[node.id]
        raw_risky = risky_policy[node.id]
        if len(raw_risky) != n or any(not finite_economic_number(v) or v < 0 for v in raw_risky):
            return unknown("INEXACT_WITNESS")
        risky = tuple(map(Q, raw_risky))
        if not within_budget(risky):
            return unknown("INEXACT_WITNESS")
        due = (
            ZERO
            if problem.node_outflow_after_contribution_r is None
            else Q(problem.node_outflow_after_contribution_r[node.id])
        )
        cost = tuple(map(Q, node.turnover_cost))
        margins = tuple(map(Q, node.initial_margin))
        turnover = tuple(abs(a - b) for a, b in zip(risky, old, strict=True))
        equity = (
            1
            + dot(incoming, x)
            - due
            - sum((a * b for a, b in zip(cost, turnover, strict=True)), ZERO)
        )
        if equity < sum((a * m for a, m in zip(risky, margins, strict=True)), ZERO):
            return unknown("INEXACT_WITNESS")
        net = equity - sum(risky, ZERO)
        x[j : j + width] = [*risky, max(ZERO, net), max(ZERO, -net), *turnover]
        funded_cap = 1 + wealth_cap
        risky_caps = [funded_cap / m for m in margins]
        cap[j : j + width] = [
            *risky_caps,
            funded_cap,
            sum(risky_caps, ZERO),
            *(a + b for a, b in zip(risky_caps, old_cap, strict=True)),
        ]
        if not within_budget((*x[j : j + width], *cap[j : j + width], probabilities[node.id])):
            return unknown("EXACT_WITNESS_RESOURCE_SCOPE")
        row = {i: -a for i, a in incoming.items()}
        row.update({j + i: Q(1) for i in range(n)})
        row.update({j + n: Q(1), j + n + 1: Q(-1)})
        row.update({j + n + 2 + i: k for i, k in enumerate(cost)})
        eq.append((row, 1 - due))
        for i in range(n):
            buy = {j + i: Q(1), j + n + 2 + i: Q(-1)}
            sell = {j + i: Q(-1), j + n + 2 + i: Q(-1)}
            if node.parent is not None:
                p = offsets[node.parent]
                buy[p + i], sell[p + i] = -Q(node.risky_gross[i]), Q(node.risky_gross[i])
            ub.extend(((buy, ZERO), (sell, ZERO)))
        margin = {j + i: m - 1 for i, m in enumerate(margins)}
        margin.update({j + n: Q(-1), j + n + 1: Q(1)})
        ub.append((margin, ZERO))

    # Recheck canonical witness against the complete exact closed polyhedron.
    ub.extend(({j: -a for j, a in row.items()}, ZERO) for row in arrivals)
    ub.extend(({j: -a for j, a in row.items()}, -liability) for row, liability, _ in leaves)
    if (
        any(dot(row, x) != rhs for row, rhs in eq)
        or any(dot(row, x) > rhs for row, rhs in ub)
        or any(not 0 <= a <= b for a, b in zip(x, cap, strict=True))
    ):
        return unknown("INEXACT_WITNESS")
    grad = [ZERO] * size
    for row, liability, probability in leaves:
        wealth = dot(row, x) - liability
        if (
            gamma * max(wealth.numerator.bit_length(), wealth.denominator.bit_length())
            > _MAX_EXACT_BITS
        ):
            return unknown("EXACT_WITNESS_RESOURCE_SCOPE")
        factor = probability / wealth**gamma
        for j, a in row.items():
            grad[j] += factor * a
        if not within_budget(grad):
            return unknown("EXACT_WITNESS_RESOURCE_SCOPE")

    # Exact dual correction: for any y>=0, lambda unrestricted,
    # g*x <= b*y+d*lambda+sum(max(0,g-A'y-E'lambda)*cap).
    # All coefficient products are rational, including original margin*gross.
    try:
        proposal = DualProposal(
            tuple(map(float, inequality_multipliers)), tuple(map(float, equality_multipliers))
        )
        y = [max(ZERO, -Q(v)) for v in proposal.inequality_marginals]
        lam = [-Q(v) for v in proposal.equality_marginals]
    except TypeError, ValueError, OverflowError:
        return unknown("MALFORMED_DUAL_PROPOSAL")
    if len(y) != len(ub) or len(lam) != len(eq):
        return unknown("MALFORMED_DUAL_PROPOSAL")
    residual = grad.copy()
    upper = ZERO
    for multiplier, (row, rhs) in zip((*y, *lam), (*ub, *eq), strict=True):
        upper += multiplier * rhs
        for j, a in row.items():
            residual[j] -= multiplier * a
        if not within_budget((upper, *(residual[j] for j in row))):
            return unknown("EXACT_WITNESS_RESOURCE_SCOPE")
    gap = upper
    for r, c, g, a in zip(residual, cap, grad, x, strict=True):
        gap += max(ZERO, r) * c - g * a
        if not within_budget((gap,)):
            return unknown("EXACT_WITNESS_RESOURCE_SCOPE")
    if gap < 0:
        return unknown("INCONSISTENT_EXACT_BOUND")
    try:
        result = float(gap)
        if Q(result) < gap:
            result = math.nextafter(result, math.inf)
    except OverflowError, ValueError:
        return unknown("UNREPRESENTABLE_EXACT_BOUND")
    if not math.isfinite(result):
        return unknown("UNREPRESENTABLE_EXACT_BOUND")
    return OptimalityEvidence(
        numerical_estimate,
        result,
        "EXACT_RATIONAL_CANONICAL_WITNESS_GAP_UPPER",
        "EXACT_INPUT_CONDITIONAL_PROBABILITIES_AND_RECONSTRUCTED_CASH_DEBT_TURNOVER",
        proposal,
    )


def verify_canonical_gap_claim(
    problem: MultistageProblem,
    risky_policy: dict[str, tuple[float, ...]],
    claim: OptimalityEvidence,
) -> bool:
    """Replay a supplied exact claim with the pure rational checker.

    False means not verified, including UNKNOWN; it does not assert that the
    economic policy is false or infeasible. No optimizer is called.
    """
    if (
        claim.standing != "EXACT_RATIONAL_CANONICAL_WITNESS_GAP_UPPER"
        or claim.dual_proposal is None
    ):
        return False
    if (
        not finite_economic_number(claim.numerical_tangent_gap_estimate)
        or claim.numerical_tangent_gap_estimate < 0
    ):
        return False
    proposal = claim.dual_proposal
    return claim == certify_canonical_gap(
        problem,
        risky_policy,
        proposal.inequality_marginals,
        proposal.equality_marginals,
        claim.numerical_tangent_gap_estimate,
    )
