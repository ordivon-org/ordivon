"""Pure shared economic input contract; no solver, provider or effects."""

from __future__ import annotations

import math


class AlgebraicPolicyError(ValueError):
    """Provided economic inputs are infeasible or not well-defined."""


def finite_economic_number(value: object) -> bool:
    """Economic scalar input, not an implicitly coerced boolean/string.

    The numerical solver uses floating-point arithmetic; out-of-range
    integers must fail at admission rather than in the optimizer.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False

