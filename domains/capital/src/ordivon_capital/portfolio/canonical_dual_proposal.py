"""Optional untrusted HiGHS proposal aligned to a locally prepared witness.

This is a numerical carrier, not a certificate authority. Every candidate
must pass the exact residual operator. It cannot promote an UNKNOWN witness.
"""

from __future__ import annotations

import math
from typing import Literal

from .optimality_evidence import (
    OptimalityEvidence,
    PreparedCanonicalWitness,
    certify_prepared_gap,
    freeze_dual_proposal,
)
from .policy_contract import AlgebraicPolicyError

DualProposalMethod = Literal["NUMERICAL_TANGENT", "CANONICAL_GRADIENT"]


def validate_dual_proposal_method(method: object) -> None:
    if not isinstance(method, str) or method not in ("NUMERICAL_TANGENT", "CANONICAL_GRADIENT"):
        raise AlgebraicPolicyError("unknown dual proposal method")


def improve_canonical_proposal(
    prepared: PreparedCanonicalWitness | str,
    baseline: OptimalityEvidence,
) -> tuple[OptimalityEvidence, str]:
    """At most one additional LP, with explicit retained/selected outcome."""
    if isinstance(prepared, str) or baseline.certified_canonical_gap_upper is None:
        return baseline, "BASELINE_NOT_CERTIFIED"
    import numpy as np
    from scipy.optimize import linprog
    from scipy.sparse import csr_matrix

    def matrix(rows):
        # Convert the independently reconstructed exact closed polyhedron;
        # row ordering is shared with the residual operator.
        indptr = [0]
        indices = []
        values = []
        rhs = []
        for row, bound in rows:
            for j, a in sorted(row):
                indices.append(j)
                values.append(float(a))
            indptr.append(len(indices))
            rhs.append(float(bound))
        return csr_matrix((values, indices, indptr), shape=(len(rows), len(prepared.x))), rhs

    mid = tuple((a + b) / 2 for a, b in zip(prepared.grad, prepared.grad_hi, strict=True))
    exact_scale = max(map(abs, mid))
    if exact_scale == 0:
        return baseline, "BASELINE_RETAINED_ZERO_GRADIENT"
    try:
        scale = float(exact_scale)
    except OverflowError:
        return baseline, "BASELINE_RETAINED_UNREPRESENTABLE_PROPOSAL"
    if not math.isfinite(scale) or scale <= 0:
        return baseline, "BASELINE_RETAINED_UNREPRESENTABLE_PROPOSAL"
    try:
        objective = np.asarray([-float(a / exact_scale) for a in mid])
        A_ub, b_ub = matrix(prepared.ub)
        A_eq, b_eq = matrix(prepared.eq)
        if not all(np.all(np.isfinite(v)) for v in (objective, A_ub.data, A_eq.data, b_ub, b_eq)):
            return baseline, "BASELINE_RETAINED_UNREPRESENTABLE_PROPOSAL"
        proposal = linprog(
            objective,
            A_ub=A_ub,
            b_ub=b_ub,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=(0.0, None),
            method="highs",
            options={"time_limit": 5.0},
        )
        if not proposal.success:
            return baseline, "BASELINE_RETAINED_PROPOSAL_FAILED"
        dual = freeze_dual_proposal(
            proposal.ineqlin.marginals,
            proposal.eqlin.marginals,
            (len(prepared.ub), len(prepared.eq)),
        )
        if dual is None:
            return baseline, "BASELINE_RETAINED_MALFORMED_PROPOSAL"
        y = tuple(v * scale for v in dual.inequality_marginals)
        lam = tuple(v * scale for v in dual.equality_marginals)
        if not all(map(math.isfinite, (*y, *lam))):
            return baseline, "BASELINE_RETAINED_UNREPRESENTABLE_PROPOSAL"
    except ValueError, TypeError, OverflowError, AttributeError:
        return baseline, "BASELINE_RETAINED_PROPOSAL_FAILED"
    candidate = certify_prepared_gap(
        prepared,
        y,
        lam,
        baseline.numerical_tangent_gap_estimate,
    )
    bound = candidate.certified_canonical_gap_upper
    if bound is not None and bound < baseline.certified_canonical_gap_upper:
        return candidate, "CANONICAL_GRADIENT_SELECTED"
    return baseline, "BASELINE_RETAINED_NO_IMPROVEMENT"
