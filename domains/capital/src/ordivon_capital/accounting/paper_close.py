"""Deterministic USD paper-account valuation for admitted long-only fills."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

MARKET_TIME = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class PaperFill:
    fill_id: str
    symbol: str
    shares: int
    price_minor: int
    fee_minor: int
    decided_at: datetime
    filled_at: datetime
    settlement_date: date | None = None


@dataclass(frozen=True)
class PaperBuy(PaperFill):
    @property
    def cost_minor(self) -> int:
        return self.shares * self.price_minor + self.fee_minor


@dataclass(frozen=True)
class PaperSell(PaperFill):
    @property
    def proceeds_minor(self) -> int:
        return self.shares * self.price_minor - self.fee_minor


@dataclass(frozen=True)
class PaperSession:
    session: date
    previous_session: date | None
    contribution_minor: int
    reserve_contribution_minor: int
    marks: dict[str, int]
    buys: tuple[PaperBuy, ...]
    sells: tuple[PaperSell, ...] = ()


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
    settlement_dates: dict[str, str] = field(default_factory=dict)

    pending_sales: dict[str, int] = field(default_factory=dict)
    sale_settlement_dates: dict[str, str] = field(default_factory=dict)
    receivable_minor: int = 0

    def payable_due_on(self, session: date) -> dict[str, int]:
        return _due_amounts(self.pending, self.settlement_dates, session)

    def receivable_due_on(self, session: date) -> dict[str, int]:
        return _due_amounts(self.pending_sales, self.sale_settlement_dates, session)


def _due_amounts(amounts: dict[str, int], dates: dict[str, str], session: date) -> dict[str, int]:
    end = session.isoformat()
    return {fill_id: amount for fill_id, amount in amounts.items() if dates.get(fill_id, end) <= end}


def _is_amount(value: int) -> bool:
    return type(value) is int and 0 <= value < 2**64


def _validate_fill(fill: PaperFill, day: PaperSession, pending: dict[str, int], side: str) -> None:
    if (
        not fill.fill_id.strip()
        or not fill.symbol.strip()
        or fill.fill_id in pending
        or not _is_amount(fill.shares)
        or not fill.shares
        or not _is_amount(fill.price_minor)
        or not fill.price_minor
        or not _is_amount(fill.fee_minor)
    ):
        raise ValueError(f"invalid or duplicate paper {side}")
    if (
        fill.decided_at.utcoffset() is None
        or fill.filled_at.utcoffset() is None
        or fill.decided_at.astimezone(UTC) >= fill.filled_at.astimezone(UTC)
        or fill.decided_at.astimezone(MARKET_TIME).date() != day.previous_session
        or fill.filled_at.astimezone(MARKET_TIME).date() != day.session
    ):
        raise ValueError(f"paper {side} violates the time boundary")
    if fill.settlement_date is not None and (
        type(fill.settlement_date) is not date or fill.settlement_date <= day.session
    ):
        raise ValueError(f"paper {side} settlement must follow the trade date")


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
    cash = day.contribution_minor
    protected = day.reserve_contribution_minor
    pending: dict[str, int] = {}
    settlement_dates: dict[str, str] = {}
    pending_sales: dict[str, int] = {}
    sale_settlement_dates: dict[str, str] = {}
    settled_sale_proceeds = 0
    if previous:
        due = previous.payable_due_on(day.session)
        due_sales = previous.receivable_due_on(day.session)
        settled_sale_proceeds = sum(due_sales.values())
        cash += previous.cash_minor - sum(due.values()) + settled_sale_proceeds
        protected += previous.protected_minor
        pending = {fill_id: amount for fill_id, amount in previous.pending.items() if fill_id not in due}
        settlement_dates = {fill_id: previous.settlement_dates[fill_id] for fill_id in pending}
        pending_sales = {
            fill_id: amount for fill_id, amount in previous.pending_sales.items()
            if fill_id not in due_sales
        }
        sale_settlement_dates = {
            fill_id: previous.sale_settlement_dates[fill_id] for fill_id in pending_sales
        }

    # Only shares carried into the session can be sold in this daily model.
    for fill in day.sells:
        _validate_fill(fill, day, pending_sales, "sell")
        if fill.settlement_date is None or not _is_amount(fill.proceeds_minor) or not fill.proceeds_minor:
            raise ValueError("paper sell requires positive net proceeds and an explicit settlement date")
        shares = positions.get(fill.symbol, 0) - fill.shares
        if shares < 0:
            raise ValueError("paper sell exceeds held shares")
        if shares:
            positions[fill.symbol] = shares
        else:
            del positions[fill.symbol]
        pending_sales[fill.fill_id] = fill.proceeds_minor
        sale_settlement_dates[fill.fill_id] = fill.settlement_date.isoformat()

    for fill in day.buys:
        _validate_fill(fill, day, pending, "buy")
        if not _is_amount(fill.cost_minor):
            raise ValueError("invalid paper buy amount")
        if fill.settlement_date is not None:
            settlement_dates[fill.fill_id] = fill.settlement_date.isoformat()
        positions[fill.symbol] = positions.get(fill.symbol, 0) + fill.shares
        pending[fill.fill_id] = fill.cost_minor
    payable = sum(pending.values())
    # A settlement date alone does not prove cash was available at the intraday buy.
    if cash - payable - settled_sale_proceeds < protected:
        raise ValueError("paper buy would consume protected cash or overdraw settled cash")
    if positions.keys() - day.marks.keys():
        raise ValueError("missing closing mark for a held instrument")
    if any(not _is_amount(day.marks[symbol]) or not day.marks[symbol] for symbol in positions):
        raise ValueError("invalid closing mark")
    market_value = sum(shares * day.marks[symbol] for symbol, shares in positions.items())
    receivable = sum(pending_sales.values())
    return PaperValuation(
        day.session, cash, protected, positions, pending, day.contribution_minor,
        payable, cash + market_value - payable + receivable, settlement_dates,
        pending_sales, sale_settlement_dates, receivable,
    )


def _decode_fill(fill: dict) -> dict:
    return fill | {
        "decided_at": datetime.fromisoformat(fill["decided_at"]),
        "filled_at": datetime.fromisoformat(fill["filled_at"]),
        "settlement_date": date.fromisoformat(fill["settlement_date"])
        if fill.get("settlement_date") is not None else None,
    }


def decode_session(payload: dict) -> PaperSession:
    return PaperSession(
        **(payload | {
            "session": date.fromisoformat(payload["session"]),
            "previous_session": date.fromisoformat(payload["previous_session"])
            if payload["previous_session"] is not None else None,
            "buys": tuple(PaperBuy(**_decode_fill(fill)) for fill in payload["buys"]),
            "sells": tuple(PaperSell(**_decode_fill(fill)) for fill in payload.get("sells", ())),
        })
    )
