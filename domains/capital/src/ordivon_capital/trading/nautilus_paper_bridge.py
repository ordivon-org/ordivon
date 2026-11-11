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


def _positive_integer(value: Any, field: str, *, allow_zero: bool = False) -> int:
    if isinstance(value, bool):
        raise NautilusPaperBridgeError(f"{field}: boolean not accepted")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise NautilusPaperBridgeError(f"{field}: invalid decimal") from exc
    if (not number.is_finite() or (number < 0 if allow_zero else number <= 0)
        or number != number.to_integral_value()):
        raise NautilusPaperBridgeError(f"{field}: nonnegative integral share quantity required")
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


def _report_rows(rows: Any, label: str) -> Sequence[Mapping[str, Any]]:
    """Retain the actual native ReportProvider client_order_id DataFrame index.

    This converts shape, not provider provenance, event-history completeness or fills.
    """
    if hasattr(rows, "reset_index") and hasattr(rows, "index"):
        if getattr(rows.index, "name", None) != "client_order_id":
            raise NautilusPaperBridgeError(f"{label}: native client_order_id index required")
        rows = rows.reset_index().to_dict(orient="records")
    if isinstance(rows, (str, bytes, Mapping)) or not isinstance(rows, Sequence):
        raise NautilusPaperBridgeError(f"{label}: sequence of report mappings required")
    if any(not isinstance(row, Mapping) for row in rows):
        raise NautilusPaperBridgeError(f"{label}: nonmapping native report row")
    return rows


def next_open_paper_session(
    *,
    session: date,
    previous_session: date,
    expected_account_id: str,
    opens_at: datetime,
    previous_close_at: datetime,
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
    expected_account_id binds all native rows to one account; PG account_key
    authorization and the event-history source remain external consumer contracts.
    The supplied event history is NOT an independently verified complete trace.
    """
    if type(session) is not date or type(previous_session) is not date or session <= previous_session:
        raise NautilusPaperBridgeError("consecutive session identity required")
    if type(settlement_date) is not date or settlement_date <= session:
        raise NautilusPaperBridgeError("settlement must follow trade session")
    opening = _instant(opens_at, "opens_at")
    prior_close = _instant(previous_close_at, "previous_close_at")
    if (prior_close.astimezone(_NY).date() != previous_session or prior_close >= opening):
        raise NautilusPaperBridgeError("previous close must precede next session open")
    if opening.astimezone(_NY).date() != session:
        raise NautilusPaperBridgeError("open instant must belong to trade session")
    if order_events is None:
        raise NautilusPaperBridgeError("native order event history required to detect corrections")
    account_scope = _required({"account_id": expected_account_id}, "account_id")
    orders = _report_rows(orders, "orders")
    fills = _report_rows(fills, "fills")

    report_orders: dict[str, Mapping[str, Any]] = {}
    for order in orders:
        client_id = _required(order, "client_order_id")
        if _required(order, "account_id") != account_scope:
            raise NautilusPaperBridgeError("order outside bound paper account")
        if client_id in report_orders:
            raise NautilusPaperBridgeError("duplicate client order identity")
        report_orders[client_id] = order

    counts: Counter[tuple[str, str]] = Counter()
    seen_event_ids: set[str] = set()
    fill_events: dict[tuple[str, str], Mapping[str, Any]] = {}
    for event in order_events:
        kind = _required(event, "type")
        if kind == "OrderFillVoided":
            raise NautilusPaperBridgeError("voided fill is not supported by immutable paper close")
        if kind != "OrderFilled":
            if kind.startswith("OrderFill"):
                raise NautilusPaperBridgeError("unsupported native fill correction event")
            continue
        identity = (_required(event, "client_order_id"), _required(event, "trade_id"))
        event_id = _required(event, "event_id")
        if event_id in seen_event_ids:
            raise NautilusPaperBridgeError("duplicate event identity")
        seen_event_ids.add(event_id)
        counts[identity] += 1
        fill_events[identity] = event
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
        if account_id != account_scope:
            raise NautilusPaperBridgeError("fill account mismatch: outside bound paper account")
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
        if (fill_time != opening or decision_time < prior_close
            or decision_time > order_init or order_init > fill_time
            or decision_time.astimezone(_NY).date() != previous_session):
            raise NautilusPaperBridgeError("outside prior-session-decision/next-open fill scope")
        side = _required(row, "order_side")
        if side not in {"BUY", "SELL"}:
            raise NautilusPaperBridgeError("unsupported execution side")
        quantity = _positive_integer(row.get("last_qty"), "last_qty")
        price_minor = _cents(row.get("last_px"), "last_px")
        fee_minor = _fee_cents(row.get("commission"))
        event = fill_events[identity]
        if _required(row, "event_id") != _required(event, "event_id"):
            raise NautilusPaperBridgeError("native event and fills report event identity disagree")
        if any(key not in event for key in ("last_qty", "last_px", "commission", "ts_event")):
            raise NautilusPaperBridgeError("native event lacks economic fill witness")
        if (_positive_integer(event["last_qty"], "event.last_qty") != quantity
            or _cents(event["last_px"], "event.last_px") != price_minor
            or _fee_cents(event["commission"]) != fee_minor
            or _instant(event["ts_event"], "event.ts_event") != fill_time):
            raise NautilusPaperBridgeError("native event and fills report economics disagree")
        if any(_required(event, field) != expected for field, expected in (
            ("account_id", account_id), ("instrument_id", instrument_id),
            ("order_side", side), ("currency", "USD"),
        )):
            raise NautilusPaperBridgeError("native event and fills report identity disagree")
        if "side" in order and _required(order, "side") != side:
            raise NautilusPaperBridgeError("native order and fill execution sides disagree")
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


def next_open_native_paper_session(
    *,
    node: Any,
    run_config_id: Any,
    session: date,
    previous_session: date,
    expected_account_id: str,
    opens_at: datetime,
    previous_close_at: datetime,
    settlement_date: date,
    decisions_by_order: Mapping[str, datetime],
    instrument_symbols: Mapping[str, str],
    marks_minor: Mapping[str, int],
    contribution_minor: int = 0,
    reserve_contribution_minor: int = 0,
) -> PaperSession:
    """Consume reports and the complete *retained native engine-cache* order history.

    Reports and order events are read from the same BacktestNode/run_config_id
    rather than accepted as independently caller-filtered collections. Engine
    state must be retained with dispose_on_completion=False. This witnesses only
    the current simulated engine cache; it does NOT attest external venue
    completeness, data availability, model validity, or PG account authorization.
    """
    try:
        orders_report = node.generate_orders_report(run_config_id)
        fills_report = node.generate_fills_report(run_config_id)
        cache = node.get_engine_cache(run_config_id)
        cached_orders = cache.orders()
    except (AttributeError, KeyError, LookupError, ValueError, TypeError) as exc:
        raise NautilusPaperBridgeError("native run reports and engine cache unavailable") from exc

    orders = _report_rows(orders_report, "native orders")
    fills = _report_rows(fills_report, "native fills")
    if not cached_orders or not orders:
        # An empty disposed engine looks like a valid zero-order run; do not
        # silently promote that absence to evidence of no execution.
        raise NautilusPaperBridgeError("empty native cache cannot witness order history")

    cached_ids: set[str] = set()
    native_events: list[Mapping[str, Any]] = []
    for native_order in cached_orders:
        client_id = str(getattr(native_order, "client_order_id", ""))
        if not client_id or client_id in cached_ids:
            raise NautilusPaperBridgeError("native cache has empty or duplicate order identity")
        cached_ids.add(client_id)
        try:
            events = native_order.events()
        except (AttributeError, ValueError, TypeError) as exc:
            raise NautilusPaperBridgeError("native order event history unavailable") from exc
        if not events:
            raise NautilusPaperBridgeError("native order has no events")
        for event in events:
            try:
                record = event.to_dict()
            except (AttributeError, ValueError, TypeError) as exc:
                raise NautilusPaperBridgeError("native order event projection unavailable") from exc
            if not isinstance(record, Mapping):
                raise NautilusPaperBridgeError("native event must project to a mapping")
            if _required(record, "type") != type(event).__name__:
                raise NautilusPaperBridgeError("native event type and runtime object disagree")
            if _required(record, "client_order_id") != client_id:
                raise NautilusPaperBridgeError("native event belongs to a different cached order")
            native_events.append(record)

    report_ids = [_required(order, "client_order_id") for order in orders]
    if len(report_ids) != len(set(report_ids)) or set(report_ids) != cached_ids:
        raise NautilusPaperBridgeError("native report and cache order inventories disagree")
    # A native Order report is a second, independent witness of the aggregate
    # filled shares. Individual event equivalence alone does not prove that
    # each order's total is conserved.
    totals: Counter[str] = Counter()
    for fill in fills:
        totals[_required(fill, "client_order_id")] += _positive_integer(
            fill.get("last_qty"), "native fill quantity"
        )
    for order in orders:
        quantity = _positive_integer(order.get("quantity"), "native order quantity")
        filled = _positive_integer(
            order.get("filled_qty"), "native order filled quantity", allow_zero=True,
        )
        if filled > quantity or filled != totals[_required(order, "client_order_id")]:
            raise NautilusPaperBridgeError("native order filled quantity and fill reports disagree")
    # Every report fill and every cached OrderFilled must agree in the base bridge.
    # It also rejects native correction/void events, off-open executions,
    # fractional shares, unsupported money and mixed account scopes.
    return next_open_paper_session(
        session=session,
        previous_session=previous_session,
        expected_account_id=expected_account_id,
        opens_at=opens_at,
        previous_close_at=previous_close_at,
        settlement_date=settlement_date,
        orders=orders,
        decisions_by_order=decisions_by_order,
        fills=fills,
        order_events=native_events,
        instrument_symbols=instrument_symbols,
        marks_minor=marks_minor,
        contribution_minor=contribution_minor,
        reserve_contribution_minor=reserve_contribution_minor,
    )
