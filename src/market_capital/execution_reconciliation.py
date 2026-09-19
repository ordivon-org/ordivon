from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


class ReconciliationError(ValueError):
    pass


# FIX lifecycle vocabulary only. Venue facts remain authoritative; FIX 4.4 remains a legacy wire profile.
_BINANCE_FIX = {
    'NEW': ('0', '0'),               # ExecType=New, OrdStatus=New
    'PARTIALLY_FILLED': ('F', '1'),  # ExecType=Trade, OrdStatus=PartiallyFilled
    'FILLED': ('F', '2'),            # ExecType=Trade, OrdStatus=Filled
    'PENDING_CANCEL': ('6', '6'),    # PendingCancel
    'CANCELED': ('4', '4'),          # Canceled
    'REJECTED': ('8', '8'),          # Rejected
    'EXPIRED': ('C', 'C'),           # Expired
}
_OKX_FIX = {
    'live': ('0', '0'),
    'partially_filled': ('F', '1'),
    'filled': ('F', '2'),
    'canceled': ('4', '4'),
    'mmp_canceled': ('4', '4'),
}

_TERMINAL_ZERO = {('4', '4'), ('8', '8'), ('C', 'C')}


_RESOLUTION_BY_STANDING = {
    "UNKNOWN": "NO_MUTATION",
    "AMBIGUOUS": "NO_MUTATION",
    "PARTIAL_OPEN": "NO_MUTATION",
    "CONTRADICTORY": "NO_MUTATION",
    "PROVEN_NO_EFFECT": "VOID_PENDING_TRANSFER",
    "RECONCILED_ZERO_FILL_TERMINAL": "VOID_PENDING_TRANSFER",
    "POSITIVE_EXECUTION": "POST_PENDING_TRANSFER",
}


def reservation_resolution_for_standing(standing: str) -> str:
    try:
        return _RESOLUTION_BY_STANDING[standing]
    except KeyError as exc:
        raise ReconciliationError(f"unsupported reconciliation standing: {standing}") from exc


def _dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value if value is not None else '0'))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ReconciliationError(f'invalid decimal: {value!r}') from exc


def _status_to_fix(venue: str, status: str | None) -> tuple[str | None, str | None]:
    if not status:
        return None, None
    if venue == 'BINANCE':
        return _BINANCE_FIX.get(status.upper(), (None, None))
    if venue == 'OKX':
        return _OKX_FIX.get(status.lower(), (None, None))
    raise ReconciliationError(f'unsupported venue: {venue}')


def _find_orders(snapshot: dict[str, Any], client_order_id: str) -> list[dict[str, Any]]:
    rows=[]
    for bucket in ('openOrders','orderHistory'):
        for row in snapshot.get(bucket) or []:
            if isinstance(row,dict) and row.get('clientOrderId') == client_order_id:
                rows.append(row)
    return rows


def _matched_fills(snapshot: dict[str, Any], matched_orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order_ids={str(r.get('venueOrderId')) for r in matched_orders if r.get('venueOrderId') is not None}
    if not order_ids:
        return []
    return [r for r in snapshot.get('fills') or [] if isinstance(r,dict) and str(r.get('venueOrderId')) in order_ids]


def reconcile_fix_intent(
    *,
    intent: dict[str, Any],
    reality: dict[str, Any],
    exact_lookup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if intent.get('protocol') != 'FIX.4.4' or intent.get('msgType') != 'D':
        raise ReconciliationError('intent must be FIX 4.4 NewOrderSingle')
    venue=str(intent.get('exDestination') or '').upper()
    if reality.get('venue') != venue:
        raise ReconciliationError('intent venue and reality venue differ')
    if reality.get('externalFinancialWriteAttempted') is not False:
        raise ReconciliationError('reality snapshot is not read-only evidence')
    if reality.get('permissionStanding') != 'READ_ONLY_VERIFIED':
        standing='UNKNOWN'
        return _result(intent, venue, standing, None, [], 'private read permission not verified')

    clid=str(intent.get('clOrdId') or '')
    if not clid:
        raise ReconciliationError('FIX ClOrdID required')
    orders=_find_orders(reality,clid)
    fills=_matched_fills(reality,orders)

    if fills:
        order=orders[-1] if orders else None
        exec_type,ord_status=_status_to_fix(venue,(order or {}).get('status'))
        lifecycle=_lifecycle(order,exec_type or 'F',ord_status or '2') if order else {'execType':'F','ordStatus':'2'}
        return _result(intent,venue,'POSITIVE_EXECUTION',lifecycle,fills,'authoritative venue fill observed')

    if orders:
        order=orders[-1]
        executed=_dec(order.get('executedQty','0'))
        exec_type,ord_status=_status_to_fix(venue,order.get('status'))
        lifecycle=_lifecycle(order,exec_type,ord_status)
        if executed > 0 or ord_status in {'1','2'}:
            return _result(intent,venue,'POSITIVE_EXECUTION',lifecycle,[], 'authoritative order reports positive executed quantity')
        coverage=reality.get('coverage') or {}
        fills_complete=coverage.get('fillsComplete') is True
        if (exec_type,ord_status) in _TERMINAL_ZERO and fills_complete:
            standing='RECONCILED_ZERO_FILL_TERMINAL'
            return _result(intent,venue,standing,lifecycle,[], 'terminal zero-fill order with complete fill query')
        return _result(intent,venue,'PARTIAL_OPEN',lifecycle,[], 'order exists but effect is not terminal zero-fill or positive execution')

    if exact_lookup is not None:
        if exact_lookup.get('venue') != venue or exact_lookup.get('clientOrderId') != clid:
            raise ReconciliationError('exact lookup identity mismatch')
        if exact_lookup.get('authoritative') is not True or exact_lookup.get('querySucceeded') is not True:
            return _result(intent,venue,'UNKNOWN',None,[], 'exact lookup not authoritative/current')
        if exact_lookup.get('orderFound') is False and exact_lookup.get('fillFound') is False:
            return _result(intent,venue,'PROVEN_NO_EFFECT',None,[], 'exact authoritative order/fill lookup proved no effect')
        return _result(intent,venue,'AMBIGUOUS',None,[], 'exact lookup did not prove no effect')

    return _result(intent,venue,'UNKNOWN',None,[], 'absence from broad snapshot is not proof of no effect')


def _lifecycle(order: dict[str,Any] | None, exec_type: str | None, ord_status: str | None) -> dict[str,Any]:
    if not order:
        return {'execType':exec_type,'ordStatus':ord_status}
    original=_dec(order.get('originalQty','0'))
    cumulative=_dec(order.get('executedQty','0'))
    leaves=max(Decimal('0'),original-cumulative)
    return {
        'execType':exec_type,
        'ordStatus':ord_status,
        'cumQty':format(cumulative,'f'),
        'leavesQty':format(leaves,'f'),
        'venueOrderId':order.get('venueOrderId'),
        'clientOrderId':order.get('clientOrderId'),
    }


def _result(intent: dict[str,Any], venue: str, standing: str, lifecycle: dict[str,Any] | None, fills: list[dict[str,Any]], reason: str) -> dict[str,Any]:
    resolution = reservation_resolution_for_standing(standing)
    return {
        'schemaVersion':1,
        'kind':'ordivon.market-capital.execution-reconciliation',
        'protocol':'FIX.4.4',
        'clOrdId':intent.get('clOrdId'),
        'venue':venue,
        'standing':standing,
        'reservationResolution':resolution,
        'fixLifecycle':lifecycle,
        'matchedFillCount':len(fills),
        'reason':reason,
        'externalFinancialWriteAttempted':False,
    }
