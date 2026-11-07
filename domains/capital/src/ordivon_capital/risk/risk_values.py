"""Fail-closed numeric conversion and lossless representations for Capital risk.

This package-local module has no domain I/O, portfolio policy or model fitting.
"""

from __future__ import annotations

import math
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any


class PortfolioRiskError(ValueError):
    """Fail-closed validation error for the read-only portfolio risk observatory."""


def _d(value: Any, label: str) -> Decimal:
    try:
        out = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise PortfolioRiskError(f"invalid decimal for {label}") from exc
    if not out.is_finite():
        raise PortfolioRiskError(f"non-finite decimal for {label}")
    return out


def _fmt_lossless(value: Decimal) -> str:
    """Keep six display places only if they preserve the exact Decimal.

    Decimal.quantize uses the caller's context precision and can raise
    InvalidOperation for an otherwise valid large notional. Decimal's native
    fixed-point formatter has no such context-precision restriction.
    """
    displayed = format(value, ".6f")
    return displayed if Decimal(displayed) == value else format(value, "f")


def _add_exact(a: Decimal, b: Decimal) -> Decimal:
    """Use Decimal's native context at the precision needed for an exact sum.

    The default 28 significant digits may silently erase small positions
    when large positive/negative notionals cancel.
    """
    highest_digit = max(a.adjusted(), b.adjusted())
    lowest_place = min(a.as_tuple().exponent, b.as_tuple().exponent)
    with localcontext() as context:
        context.prec = max(context.prec, highest_digit - lowest_place + 2)
        return a + b


def _multiply_exact(a: Decimal, b: Decimal) -> Decimal:
    """Products of finite Decimal coefficients fit within their digit sum."""
    with localcontext() as context:
        context.prec = max(
            context.prec, len(a.as_tuple().digits) + len(b.as_tuple().digits) + 1
        )
        return a * b


def _float(value: Any, label: str) -> float:
    out = float(_d(value, label))
    if not math.isfinite(out):
        raise PortfolioRiskError(f"non-finite float for {label}")
    return out
