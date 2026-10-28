"""One shared market-data LEGO: qualified public best bid/offer (BBO).

Truth predicate: finite positive bid and ask with bid <= ask.
This permits bounded observation only; it does not establish a trade, arb,
venue availability, order fill, timestamp integrity, or execution permission.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


def qualified_public_bbo(bid: Any, ask: Any, *, source: str) -> tuple[Decimal, Decimal]:
    """Return exact prices, or reject unqualified public quote data."""
    try:
        prices = Decimal(str(bid)), Decimal(str(ask))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{source}: non-decimal public BBO") from exc
    best_bid, best_ask = prices
    if (
        not best_bid.is_finite()
        or not best_ask.is_finite()
        or best_bid <= 0
        or best_ask <= 0
        or best_bid > best_ask
    ):
        raise ValueError(f"{source}: BBO must satisfy 0 < bid <= ask with finite prices")
    return prices
