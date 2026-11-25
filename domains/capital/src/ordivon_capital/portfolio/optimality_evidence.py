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
from collections.abc import Iterable, Mapping, Set
from dataclasses import dataclass
from fractions import Fraction
from itertools import islice
from typing import Any

from .information_tree import MultistageProblem, ValidatedInformationTree, validate_information_tree
from .policy_contract import AlgebraicPolicyError, finite_economic_number
from .rational_enclosure import enclose_inverse_power, enclose_rational

Q = Fraction
ZERO = Q(0)
_MAX_EXACT_BITS = 16_384
_MAX_EXACT_NODES = 63
_MAX_EXACT_ASSETS = 16
_RATIONAL_REASON = "EXACT_INPUT_CONDITIONAL_PROBABILITIES_AND_RECONSTRUCTED_CASH_DEBT_TURNOVER"
_DYADIC_REASON = "EXACT_DYADIC_GRADIENT_ENCLOSURE_AND_CANONICAL_WITNESS"


def _within_bit_budget(values: Iterable[Fraction]) -> bool:
    return all(
        max(v.numerator.bit_length(), v.denominator.bit_length()) <= _MAX_EXACT_BITS for v in values
    )


@dataclass(frozen=True)
class DualProposal:
    inequality_marginals: tuple[float, ...]
    equality_marginals: tuple[float, ...]


def proof_dual_dimensions(tree: ValidatedInformationTree) -> tuple[int, int] | None:
    """Finite receipt coordinate budget; not an economic admission rule."""
    if len(tree.ordered) > _MAX_EXACT_NODES or tree.asset_count > _MAX_EXACT_ASSETS:
        return None
    d = len(tree.decision)
    # Non-root maintenance + arrivals, local turnover/margin, terminal surplus.
    return 2 * (len(tree.ordered) - 1) + (2 * tree.asset_count + 1) * d + len(tree.leaves), d


def freeze_dual_proposal(
    inequality_multipliers: Any,
    equality_multipliers: Any,
    dimensions: tuple[int, int],
) -> DualProposal | None:
    """Reject excess or malformed coordinates without exhausting iterators.

    The finite consumption bound is count-based; it is not a wall-time
    sandbox for arbitrary caller-provided Python iterator implementations.
    """

    def coordinates(values: Any, count: int) -> tuple[float, ...] | None:
        if isinstance(values, (str, bytes, bytearray, Mapping, Set)):
            return None
        try:
            raw = tuple(islice(iter(values), count + 1))
            if len(raw) != count or any(not finite_economic_number(v) for v in raw):
                return None
            return tuple(map(float, raw))
        except TypeError, ValueError, OverflowError:
            return None

    y = coordinates(inequality_multipliers, dimensions[0])
    if y is None:
        return None
    lam = coordinates(equality_multipliers, dimensions[1])
    if lam is None:
        return None
    return DualProposal(y, lam)


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
    *,
    gradient_method: str = "AUTO",
) -> OptimalityEvidence:
    """Bound optimum minus utility of a reconstructed exact feasible policy.

    Supplied multipliers are untrusted proposals, even if numerically optimal.
    Exact residual correction over finite canonical boxes gives weak duality.
    Resource scope limits qualification, never the admitted economic model.
    """

    def unknown(reason: str) -> OptimalityEvidence:
        return OptimalityEvidence(numerical_estimate, None, "UNKNOWN", reason)

    if not finite_economic_number(numerical_estimate) or numerical_estimate < 0:
        raise AlgebraicPolicyError("finite nonnegative numerical estimate required")

    tree = validate_information_tree(problem)
    gamma_q = Q(problem.gamma)
    if not 0 < gamma_q <= 16 or gamma_q.denominator > 16:
        return unknown("DYADIC_GAMMA_UP_TO_16_WITH_DENOMINATOR_AT_MOST_16_ONLY")
    dimensions = proof_dual_dimensions(tree)
    if dimensions is None:
        return unknown("EXACT_WITNESS_RESOURCE_SCOPE")
    if gradient_method == "AUTO":
        # Small integer contracts retain exact rational receipts. Larger
        # trees and fractional powers use a verified dyadic enclosure.
        gradient_method = (
            "RATIONAL" if gamma_q.denominator == 1 and len(tree.ordered) <= 15 else "DYADIC"
        )
    if gradient_method not in ("RATIONAL", "DYADIC"):
        return unknown("UNRECOGNIZED_GRADIENT_METHOD")
    if gradient_method == "RATIONAL" and gamma_q.denominator != 1:
        return unknown("RATIONAL_GRADIENT_REQUIRES_INTEGER_GAMMA")
    gamma = int(gamma_q)

    n = tree.asset_count
    width = 2 * n + 2
    offsets = {node.id: i * width for i, node in enumerate(tree.decision)}
    size = len(offsets) * width
    if (
        not isinstance(risky_policy, dict)
        or len(risky_policy) != len(offsets)
        or risky_policy.keys() != offsets.keys()
    ):
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
        if (
            not isinstance(raw_risky, tuple)
            or len(raw_risky) != n
            or any(not finite_economic_number(v) or v < 0 for v in raw_risky)
        ):
            return unknown("INEXACT_WITNESS")
        risky = tuple(map(Q, raw_risky))
        if not _within_bit_budget(risky):
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
        if not _within_bit_budget((*x[j : j + width], *cap[j : j + width], probabilities[node.id])):
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
    grad_hi = [ZERO] * size
    # Both gradients start at zero. Each leaf changes only its row support;
    # induction preserves the bit bound on every untouched coordinate.
    for row, liability, probability in leaves:
        wealth = dot(row, x) - liability
        if gradient_method == "RATIONAL":
            if (
                gamma * max(wealth.numerator.bit_length(), wealth.denominator.bit_length())
                > _MAX_EXACT_BITS
            ):
                return unknown("EXACT_WITNESS_RESOURCE_SCOPE")
            factor = probability / wealth**gamma
            for j, a in row.items():
                grad[j] += factor * a
            if not _within_bit_budget(grad[j] for j in row):
                return unknown("EXACT_WITNESS_RESOURCE_SCOPE")
        else:
            enclosure = enclose_inverse_power(wealth, gamma_q, max_bits=_MAX_EXACT_BITS)
            if enclosure is None:
                return unknown("EXACT_WITNESS_RESOURCE_SCOPE")
            low, high = enclosure
            for j, a in row.items():
                t0, t1 = sorted((a * probability * low, a * probability * high))
                grad[j] += enclose_rational(t0)[0]
                grad_hi[j] += enclose_rational(t1)[1]
            if not _within_bit_budget(v[j] for v in (grad, grad_hi) for j in row):
                return unknown("EXACT_WITNESS_RESOURCE_SCOPE")
    if gradient_method == "RATIONAL":
        grad_hi = grad

    # Exact dual correction: for any y>=0, lambda unrestricted,
    # g*x <= b*y+d*lambda+sum(max(0,g-A'y-E'lambda)*cap).
    # All coefficient products are rational, including original margin*gross.
    if dimensions != (len(ub), len(eq)):
        return unknown("INCONSISTENT_DUAL_COORDINATES")
    proposal = freeze_dual_proposal(inequality_multipliers, equality_multipliers, dimensions)
    if proposal is None:
        return unknown("MALFORMED_DUAL_PROPOSAL")
    y = [max(ZERO, -Q(v)) for v in proposal.inequality_marginals]
    lam = [-Q(v) for v in proposal.equality_marginals]
    residual = grad.copy()
    upper = ZERO
    for multiplier, (row, rhs) in zip((*y, *lam), (*ub, *eq), strict=True):
        upper += multiplier * rhs
        for j, a in row.items():
            residual[j] -= multiplier * a
        if not _within_bit_budget((upper, *(residual[j] for j in row))):
            return unknown("EXACT_WITNESS_RESOURCE_SCOPE")
    gap = upper
    for r, c, g, hi, a in zip(residual, cap, grad, grad_hi, x, strict=True):
        # If true gradient is in [g,hi], its tangent displacement is
        # at most the lower-gradient displacement plus (hi-g)*(cap-x).
        # This is an exact enclosure error, not an empirical epsilon.
        gap += max(ZERO, r) * c - g * a + (hi - g) * (c - a)
        if not _within_bit_budget((gap,)):
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
        _RATIONAL_REASON if gradient_method == "RATIONAL" else _DYADIC_REASON,
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
        not isinstance(claim, OptimalityEvidence)
        or claim.standing != "EXACT_RATIONAL_CANONICAL_WITNESS_GAP_UPPER"
        or not isinstance(claim.dual_proposal, DualProposal)
    ):
        return False
    if (
        not finite_economic_number(claim.numerical_tangent_gap_estimate)
        or claim.numerical_tangent_gap_estimate < 0
        or not finite_economic_number(claim.certified_canonical_gap_upper)
        or claim.certified_canonical_gap_upper < 0
    ):
        return False
    proposal = claim.dual_proposal
    methods = {_RATIONAL_REASON: "RATIONAL", _DYADIC_REASON: "DYADIC"}
    if not isinstance(claim.reason, str) or claim.reason not in methods:
        return False
    return claim == certify_canonical_gap(
        problem,
        risky_policy,
        proposal.inequality_marginals,
        proposal.equality_marginals,
        claim.numerical_tangent_gap_estimate,
        gradient_method=methods[claim.reason],
    )
