"""Nautilus backtest fill-report -> existing next-open PaperSession (simulation only).

This is a narrow, pure cross-framework adapter, not a new OMS, fill model,
source-of-truth, settlement engine, or proof of historical venue authority.

The existing PaperSession accepts only prior-session decisions and next-session
opening fills. Other Nautilus executions must use a different accounting
consumer rather than silently changing timestamps or widening this contract.

Pass rows from native Nautilus orders/fills reports and an order-event history
exported from the same run. The event history is caller supplied: it cannot
authenticate completeness, prove market provenance, or establish real fills.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo

from ..accounting.paper_close import PaperBuy, PaperSell, PaperSession

_NY = ZoneInfo("America/New_York")
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


class NautilusPaperBridgeError(ValueError):
    """The native execution evidence cannot refine a next-open paper close."""


def _required(row: Mapping[str, Any], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise NautilusPaperBridgeError(f"missing string {field}")
    return value


def _instant(value: Any, field: str) -> datetime:
    if isinstance(value, bool):
        raise NautilusPaperBridgeError(f"{field}: boolean is not a timestamp")
    if isinstance(value, int):
        if value < 0:
            raise NautilusPaperBridgeError(f"{field}: negative timestamp")
        # Native Nautilus ts_init / ts_event are Unix nanoseconds.
        seconds, ns = divmod(value, 1_000_000_000)
        if ns % 1_000:
            raise NautilusPaperBridgeError(f"{field}: nanosecond precision not representable")
        try:
            value = _EPOCH + timedelta(seconds=seconds, microseconds=ns // 1_000)
        except OverflowError as exc:
            raise NautilusPaperBridgeError(f"{field}: timestamp out of range") from exc
    elif isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise NautilusPaperBridgeError(f"{field}: invalid timestamp") from exc
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise NautilusPaperBridgeError(f"{field}: timezone-aware timestamp required")
    return value.astimezone(UTC)


def _positive_integer(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise NautilusPaperBridgeError(f"{field}: boolean not accepted")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise NautilusPaperBridgeError(f"{field}: invalid decimal") from exc
    if not number.is_finite() or number <= 0 or number != number.to_integral_value():
        raise NautilusPaperBridgeError(f"{field}: positive integral share quantity required")
    result = int(number)
    if result >= 2**63:
        raise NautilusPaperBridgeError(f"{field}: quantity exceeds bounded paper model")
    return result


def _cents(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise NautilusPaperBridgeError(f"{field}: boolean not accepted")
    try:
        d = Decimal(str(value))
    except InvalidOperation as exc:
        raise NautilusPaperBridgeError(f"{field}: invalid decimal") from exc
    cents = d * 100
    if not d.is_finite() or cents != cents.to_integral_value() or cents < 0 or cents >= 2**63:
        raise NautilusPaperBridgeError(f"{field}: exact nonnegative USD cents required")
    return int(cents)


def _fee_cents(value: Any) -> int:
    if not isinstance(value, str):
        raise NautilusPaperBridgeError("commission: missing native Money and currency")
    parts = value.strip().split()
    if len(parts) != 2 or parts[1] != "USD":
        raise NautilusPaperBridgeError("commission: explicit USD Money required")
    return _cents(parts[0], "commission")


def next_open_paper_session(
    *,
    session: date,
    previous_session: date,
    opens_at: datetime,
    settlement_date: date,
    orders: Sequence[Mapping[str, Any]],
    decisions_by_order: Mapping[str, datetime],
    fills: Sequence[Mapping[str, Any]],
    order_events: Sequence[Mapping[str, Any]] | None,
    instrument_symbols: Mapping[str, str],
    marks_minor: Mapping[str, int],
    contribution_minor: int = 0,
    reserve_contribution_minor: int = 0,
) -> PaperSession:
    """Project one bounded Nautilus PAPER episode; never write a ledger.

    Fills report rows require trade_id, client_order_id, account_id,
    instrument_id, order_side, last_qty, last_px, currency, commission, ts_event.
    Orders report rows require client_order_id, account_id, instrument_id,
    ts_init. DecisionAt comes separately from the upstream Portfolio consumer,
    NEVER inferred from the Nautilus order initialization. Event rows are
    OrderFilled.to_dict-style values with type,
    event_id, trade_id and client_order_id; all corrections are rejected.
    The supplied event history is NOT an independently verified complete trace.
    """
    if type(session) is not date or type(previous_session) is not date or session <= previous_session:
        raise NautilusPaperBridgeError("consecutive session identity required")
    if type(settlement_date) is not date or settlement_date <= session:
        raise NautilusPaperBridgeError("settlement must follow trade session")
    opening = _instant(opens_at, "opens_at")
    if opening.astimezone(_NY).date() != session:
        raise NautilusPaperBridgeError("open instant must belong to trade session")
    if order_events is None:
        raise NautilusPaperBridgeError("native order event history required to detect corrections")

    report_orders: dict[str, Mapping[str, Any]] = {}
    for order in orders:
        client_id = _required(order, "client_order_id")
        if client_id in report_orders:
            raise NautilusPaperBridgeError("duplicate client order identity")
        report_orders[client_id] = order

    counts: Counter[tuple[str, str]] = Counter()
    seen_event_ids: set[str] = set()
    for event in order_events:
        kind = _required(event, "type")
        if kind == "OrderFillVoided":
            raise NautilusPaperBridgeError("voided fill is not supported by immutable paper close")
        if kind != "OrderFilled":
            continue
        identity = (_required(event, "client_order_id"), _required(event, "trade_id"))
        event_id = _required(event, "event_id")
        if event_id in seen_event_ids:
            raise NautilusPaperBridgeError("duplicate event identity")
        seen_event_ids.add(event_id)
        counts[identity] += 1
        if counts[identity] > 1:
            raise NautilusPaperBridgeError("trade restatement or duplicated native fill event")

    buys: list[PaperBuy] = []
    sells: list[PaperSell] = []
    seen_fills: set[tuple[str, str]] = set()
    seen_account_trades: set[tuple[str, str]] = set()
    for row in fills:
        client_id = _required(row, "client_order_id")
        trade_id = _required(row, "trade_id")
        identity = (client_id, trade_id)
        if identity in seen_fills or counts.get(identity) != 1:
            raise NautilusPaperBridgeError("fill report and unique event history disagree")
        seen_fills.add(identity)
        order = report_orders.get(client_id)
        if order is None:
            raise NautilusPaperBridgeError("fill has no native order")
        account_id = _required(row, "account_id")
        instrument_id = _required(row, "instrument_id")
        account_trade = (account_id, trade_id)
        if account_trade in seen_account_trades:
            raise NautilusPaperBridgeError("duplicate trade identity within paper account")
        seen_account_trades.add(account_trade)
        if _required(order, "account_id") != account_id or _required(order, "instrument_id") != instrument_id:
            raise NautilusPaperBridgeError("order/fill account or instrument mismatch")
        symbol = instrument_symbols.get(instrument_id)
        if not isinstance(symbol, str) or not symbol.strip():
            raise NautilusPaperBridgeError("instrument has no explicit ETF mapping")
        if _required(row, "currency") != "USD":
            raise NautilusPaperBridgeError("only USD paper fills supported")
        fill_time = _instant(row.get("ts_event"), "ts_event")
        order_init = _instant(order.get("ts_init"), "ts_init")
        if client_id not in decisions_by_order:
            raise NautilusPaperBridgeError("missing upstream investment decision time")
        decision_time = _instant(decisions_by_order[client_id], "decision_at")
        if (fill_time != opening or decision_time > order_init or order_init > fill_time
            or decision_time.astimezone(_NY).date() != previous_session):
            raise NautilusPaperBridgeError("outside prior-session-decision/next-open fill scope")
        side = _required(row, "order_side")
        if side not in {"BUY", "SELL"}:
            raise NautilusPaperBridgeError("unsupported execution side")
        quantity = _positive_integer(row.get("last_qty"), "last_qty")
        price_minor = _cents(row.get("last_px"), "last_px")
        fee_minor = _fee_cents(row.get("commission"))
        if price_minor == 0:
            raise NautilusPaperBridgeError("zero execution price")
        fill_id = f"nautilus-paper:{account_id}:{trade_id}"
        cls = PaperBuy if side == "BUY" else PaperSell
        record = cls(
            fill_id=fill_id, symbol=symbol, shares=quantity,
            price_minor=price_minor, fee_minor=fee_minor,
            decided_at=decision_time, filled_at=fill_time,
            settlement_date=settlement_date,
        )
        (buys if side == "BUY" else sells).append(record)

    if set(counts) != seen_fills:
        raise NautilusPaperBridgeError("native events not represented in fills report")
    return PaperSession(
        session=session, previous_session=previous_session,
        contribution_minor=contribution_minor,
        reserve_contribution_minor=reserve_contribution_minor,
        marks=dict(marks_minor), buys=tuple(buys), sells=tuple(sells),
    )
