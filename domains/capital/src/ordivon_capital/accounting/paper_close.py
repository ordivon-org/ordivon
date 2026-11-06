"""Deterministic USD paper-account valuation for admitted long-only buy fills."""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

MARKET_TIME = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class PaperBuy:
    fill_id: str
    symbol: str
    shares: int
    price_minor: int
    fee_minor: int
    decided_at: datetime
    filled_at: datetime

    @property
    def cost_minor(self) -> int:
        return self.shares * self.price_minor + self.fee_minor


@dataclass(frozen=True)
class PaperSession:
    session: date
    previous_session: date | None
    contribution_minor: int
    reserve_contribution_minor: int
    marks: dict[str, int]
    buys: tuple[PaperBuy, ...]


@dataclass(frozen=True)
class PaperValuation:
    session: date
    cash_minor: int
    protected_minor: int
    positions: dict[str, int]
    pending: dict[str, int]
    contribution_minor: int
    payable_minor: int
    nav_minor: int


def _is_amount(value: int) -> bool:
    return type(value) is int and 0 <= value < 2**64


def value_session(previous: PaperValuation | None, day: PaperSession) -> PaperValuation:
    """Close one session on an upstream-validated consecutive market calendar."""
    if day.previous_session != (previous.session if previous else None) or (
        previous is not None and day.session <= previous.session
    ):
        raise ValueError("previous session does not match the account head")
    if (
        not _is_amount(day.contribution_minor)
        or not _is_amount(day.reserve_contribution_minor)
        or day.reserve_contribution_minor > day.contribution_minor
    ):
        raise ValueError("invalid contribution or protected cash")
    positions = dict(previous.positions) if previous else {}
    cash = day.contribution_minor + (previous.cash_minor - previous.payable_minor if previous else 0)
    protected = day.reserve_contribution_minor + (previous.protected_minor if previous else 0)
    pending: dict[str, int] = {}
    for fill in day.buys:
        if (
            not fill.fill_id.strip()
            or not fill.symbol.strip()
            or fill.fill_id in pending
            or not _is_amount(fill.shares)
            or not fill.shares
            or not _is_amount(fill.price_minor)
            or not fill.price_minor
            or not _is_amount(fill.fee_minor)
            or not _is_amount(fill.cost_minor)
        ):
            raise ValueError("invalid or duplicate paper buy")
        if (
            fill.decided_at.utcoffset() is None
            or fill.filled_at.utcoffset() is None
            or fill.decided_at.astimezone(UTC) >= fill.filled_at.astimezone(UTC)
            or fill.decided_at.astimezone(MARKET_TIME).date() != day.previous_session
            or fill.filled_at.astimezone(MARKET_TIME).date() != day.session
        ):
            raise ValueError("paper buy violates the time boundary")
        positions[fill.symbol] = positions.get(fill.symbol, 0) + fill.shares
        pending[fill.fill_id] = fill.cost_minor
    payable = sum(pending.values())
    if cash - payable < protected:
        raise ValueError("paper buy would consume protected cash or overdraw settled cash")
    if positions.keys() - day.marks.keys():
        raise ValueError("missing closing mark for a held instrument")
    if any(not _is_amount(day.marks[symbol]) or not day.marks[symbol] for symbol in positions):
        raise ValueError("invalid closing mark")
    market_value = sum(shares * day.marks[symbol] for symbol, shares in positions.items())
    return PaperValuation(
        day.session, cash, protected, positions, pending,
        day.contribution_minor, payable, cash + market_value - payable,
    )


def decode_session(payload: dict) -> PaperSession:
    return PaperSession(
        **(payload | {
            "session": date.fromisoformat(payload["session"]),
            "previous_session": date.fromisoformat(payload["previous_session"])
            if payload["previous_session"] is not None else None,
            "buys": tuple(
                PaperBuy(**(fill | {
                    "decided_at": datetime.fromisoformat(fill["decided_at"]),
                    "filled_at": datetime.fromisoformat(fill["filled_at"]),
                }))
                for fill in payload["buys"]
            ),
        })
    )
