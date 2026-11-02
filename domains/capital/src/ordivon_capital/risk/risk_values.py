"""Fail-closed numeric conversion and lossless representations for Capital risk.

This package-local module has no domain I/O, portfolio policy or model fitting.
"""

from __future__ import annotations

import math
from decimal import Decimal, InvalidOperation
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


def _fmt(value: Decimal | None, places: str = "0.000001") -> str | None:
    if value is None:
        return None
    return format(value.quantize(Decimal(places)), "f")


def _fmt_lossless(value: Decimal) -> str:
    """Keep the legacy six-place presentation only when it preserves the input.

    Position and factor values feed other LEGO calculations. A displayed
    rounded value is not interchangeable with the source numeric value.
    """
    displayed = _fmt(value)
    assert displayed is not None
    return displayed if Decimal(displayed) == value else format(value, "f")


def _float(value: Any, label: str) -> float:
    out = float(_d(value, label))
    if not math.isfinite(out):
        raise PortfolioRiskError(f"non-finite float for {label}")
    return out
