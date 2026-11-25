"""Numerically stable, read-only CRRA certainty-equivalent operator.

The normalized positive scenario weights define a power mean of positive
wealth. No market, solver, funding or authorization policy is owned here.
"""
from __future__ import annotations

import math
from typing import Any

from .policy_contract import AlgebraicPolicyError, finite_economic_number


def certainty_equivalent(wealth: Any, probabilities: Any, gamma: float) -> float:
    """Evaluate the power mean continuously at gamma=1 without cancellation."""
    import numpy as np
    from scipy.special import logsumexp

    w = np.asarray(wealth, dtype=float)
    p = np.asarray(probabilities, dtype=float)
    if (
        not finite_economic_number(gamma) or gamma <= 0
        or w.ndim != 1 or p.shape != w.shape or w.size == 0
        or not np.all(np.isfinite(w)) or np.any(w <= 0)
        or not np.all(np.isfinite(p)) or np.any(p <= 0) or np.any(p > 1)
    ):
        raise AlgebraicPolicyError("invalid CRRA certainty-equivalent inputs")
    total = math.fsum(float(v) for v in p)
    if not math.isclose(total, 1.0, rel_tol=1e-10, abs_tol=1e-12):
        raise AlgebraicPolicyError("CRRA probabilities must sum to one")
    # Exact deterministic identity, including extreme finite wealth/gamma.
    if np.all(w == w[0]):
        return float(w[0])
    logs = np.log(w)
    a = 1.0 - gamma
    if a == 0:
        log_ce = math.fsum(float(q * v) for q, v in zip(p, logs, strict=True)) / total
    else:
        # Choose an extremal reference so all shifted exponents are nonpositive.
        # Near zero, expm1/log1p preserves the first-order term that ordinary
        # log(sum(exp(...))) rounds away. For large spreads reuse SciPy logsumexp.
        anchor = float(np.max(logs) if a > 0 else np.min(logs))
        with np.errstate(over="ignore", under="ignore"):
            delta = a * (logs - anchor)
            if float(np.min(delta)) >= -0.5:
                perturbation = math.fsum(
                    float(q * v) for q, v in zip(p, np.expm1(delta), strict=True)
                ) / total
                correction = math.log1p(perturbation)
            else:
                correction = float(logsumexp(delta, b=p)) - math.log(total)
        log_ce = anchor + correction / a
    if not math.isfinite(log_ce):
        raise AlgebraicPolicyError("nonfinite CRRA log certainty equivalent")
    # The power mean lies between the minimum and maximum of its inputs.
    # Clamping only its log to that proven range avoids endpoint roundoff
    # overflowing exp() at the largest representable float.
    log_ce = min(float(np.max(logs)), max(float(np.min(logs)), log_ce))
    try:
        ce = math.exp(log_ce)
    except OverflowError:
        ce = float(np.max(w))
    if not math.isfinite(ce) or ce <= 0:
        raise AlgebraicPolicyError("unrepresentable CRRA certainty equivalent")
    return min(float(np.max(w)), max(float(np.min(w)), ce))
