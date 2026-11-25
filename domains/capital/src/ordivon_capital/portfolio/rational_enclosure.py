"""Outward dyadic enclosures using exact integer arithmetic.

No floating point transcendental, tolerance guess or third-party proof engine.
Only small dyadic rational exponents are qualified. The checker can decline
when an exact intermediate would exceed its declared resource envelope.
"""

from __future__ import annotations

import math
from fractions import Fraction

Q = Fraction
DYADIC_FRACTION_BITS = 96
_SCALE = 1 << DYADIC_FRACTION_BITS


def enclose_rational(value: Fraction) -> tuple[Fraction, Fraction]:
    scaled = value * _SCALE
    low = scaled.numerator // scaled.denominator
    high = -((-scaled.numerator) // scaled.denominator)
    return Q(low, _SCALE), Q(high, _SCALE)


def enclose_inverse_power(
    wealth: Fraction,
    gamma: Fraction,
    *,
    max_bits: int,
) -> tuple[Fraction, Fraction] | None:
    """Enclose wealth**(-gamma) for admitted positive dyadic gamma.

    If gamma=m/2**k, floor(2**96 * wealth**(-gamma)) is computed by
    repeated integer square roots of floor(wealth**(-m) * 2**(96*2**k)).
    Integer floor commutes with integer root. The adjacent dyadic endpoint
    is a conservative upper bound, independently of machine rounding.
    """
    if wealth <= 0 or not 0 < gamma <= 16 or gamma.denominator > 16:
        return None
    d, m = gamma.denominator, gamma.numerator
    if d & (d - 1):
        return None
    shift = DYADIC_FRACTION_BITS * d
    cost = m * max(wealth.numerator.bit_length(), wealth.denominator.bit_length())
    if cost + shift > max_bits:
        return None
    power = wealth ** (-m)
    if d == 1:
        return enclose_rational(power)
    radicand = (power.numerator << shift) // power.denominator
    for _ in range(d.bit_length() - 1):
        radicand = math.isqrt(radicand)
    return Q(radicand, _SCALE), Q(radicand + 1, _SCALE)
