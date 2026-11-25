"""Exact canonical box propagation on already validated economic coordinates.

No solver, risk authorization, or numeric approximation is owned here.
The parent margin budget couples risky holdings. The edge bound follows
from borrow >= lend and nonnegative debt; the decision bound uses canonical
cash/debt cancellation. The caller owns validation and proof bit admission.
"""

from fractions import Fraction
from typing import Literal

from .policy_contract import AlgebraicPolicyError

CapMethod = Literal["LEGACY_V1", "STRUCTURED_V2"]


def validate_cap_method(value: object) -> None:
    if not isinstance(value, str) or value not in ("LEGACY_V1", "STRUCTURED_V2"):
        raise AlgebraicPolicyError("unknown canonical cap method")


def structured_arrival_cap(
    parent_equity_cap: Fraction,
    parent_margins: tuple[Fraction, ...],
    gross: tuple[Fraction, ...],
    lend: Fraction,
) -> Fraction:
    return parent_equity_cap * (
        lend
        + max(Fraction(0), *((g - lend) / m for g, m in zip(gross, parent_margins, strict=True)))
    )


def structured_decision_caps(
    equity_cap: Fraction,
    margins: tuple[Fraction, ...],
    old_risky_caps: tuple[Fraction, ...],
) -> tuple[Fraction, ...]:
    risky = tuple(equity_cap / m for m in margins)
    debt = equity_cap * max(1 / m - 1 for m in margins)
    return (*risky, equity_cap, debt, *(a + b for a, b in zip(risky, old_risky_caps, strict=True)))
