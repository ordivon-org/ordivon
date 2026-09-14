from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Iterable


class PrivateRealityError(ValueError):
    pass


def _d(value: Any, label: str) -> str:
    try:
        return format(Decimal(str(value)), 'f')
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise PrivateRealityError(f'invalid decimal for {label}') from exc


def _call_data(call: Any) -> Any:
    if not isinstance(call, dict) or call.get('ok') is not True:
        return None
    response = call.get('response')
    if not isinstance(response, dict):
        return None
    data = response.get('data')
    # OKX native read result nests provider payload under response.data.data.
    if isinstance(data, dict) and isinstance(data.get('data'), list):
        return data['data']
    return data


def normalize_binance_observer(envelope: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(envelope, dict):
        raise PrivateRealityError('Binance observer envelope must be an object')
    if (envelope.get('extensions') or {}).get('externalFinancialWriteAttempted') is not False:
        raise PrivateRealityError('Binance observer must prove externalFinancialWriteAttempted=false')
    restrictions = (envelope.get('extensions') or {}).get('credentialRestrictions') or {}
    observed = restrictions.get('observed') or {}
    permission_safe = (
        restrictions.get('safe') is True
        and observed.get('enableReading') is True
        and observed.get('enableSpotAndMarginTrading') is False
        and observed.get('enableWithdrawals') is False
    )
    calls = envelope.get('calls') or {}
    account = _call_data(calls.get('account_get_account'))
    balances: list[dict[str, str]] = []
    if isinstance(account, dict):
        for row in account.get('balances') or []:
            if not isinstance(row, dict):
                continue
            asset = str(row.get('asset') or '').strip()
            if not asset:
                continue
            free = _d(row.get('free', '0'), f'{asset}.free')
            locked = _d(row.get('locked', '0'), f'{asset}.locked')
            total = format(Decimal(free) + Decimal(locked), 'f')
            balances.append({'asset': asset, 'available': free, 'locked': locked, 'total': total})

    open_orders: list[dict[str, Any]] = []
    order_history: list[dict[str, Any]] = []
    fills: list[dict[str, Any]] = []
    for key, call in calls.items():
        if not isinstance(key, str):
            continue
        rows = _call_data(call)
        if not isinstance(rows, list):
            continue
        if key.endswith(':account_open_orders'):
            open_orders.extend(_normalize_binance_orders(rows))
        elif key.endswith(':account_all_orders'):
            order_history.extend(_normalize_binance_orders(rows))
        elif key.endswith(':account_my_trades'):
            fills.extend(_normalize_binance_fills(rows))

    return {
        'schemaVersion': 1,
        'kind': 'ordivon.market-capital.private-reality-snapshot',
        'venue': 'BINANCE',
        'product': 'SPOT',
        'sourceAuthority': 'BINANCE_USER_DATA',
        'sourceStatus': envelope.get('status'),
        'permissionStanding': 'READ_ONLY_VERIFIED' if permission_safe else 'NOT_VERIFIED',
        'balances': sorted(balances, key=lambda x: x['asset']),
        'positions': [],
        'openOrders': open_orders,
        'orderHistory': order_history,
        'fills': fills,
        'externalFinancialWriteAttempted': False,
    }


def _normalize_binance_orders(rows: Iterable[Any]) -> list[dict[str, Any]]:
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        out.append({
            'venueOrderId': str(r.get('orderId')) if r.get('orderId') is not None else None,
            'clientOrderId': r.get('clientOrderId') or r.get('origClientOrderId'),
            'instrumentId': r.get('symbol'),
            'side': r.get('side'),
            'orderType': r.get('type'),
            'timeInForce': r.get('timeInForce'),
            'status': r.get('status'),
            'originalQty': _d(r.get('origQty', '0'), 'binance.origQty'),
            'executedQty': _d(r.get('executedQty', '0'), 'binance.executedQty'),
            'price': _d(r.get('price', '0'), 'binance.price'),
            'venueTimestampMs': r.get('updateTime') or r.get('time'),
        })
    return out


def _normalize_binance_fills(rows: Iterable[Any]) -> list[dict[str, Any]]:
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        out.append({
            'venueTradeId': str(r.get('id')) if r.get('id') is not None else None,
            'venueOrderId': str(r.get('orderId')) if r.get('orderId') is not None else None,
            'instrumentId': r.get('symbol'),
            'qty': _d(r.get('qty', '0'), 'binance.trade.qty'),
            'price': _d(r.get('price', '0'), 'binance.trade.price'),
            'commission': _d(r.get('commission', '0'), 'binance.trade.commission'),
            'commissionAsset': r.get('commissionAsset'),
            'venueTimestampMs': r.get('time'),
        })
    return out


def normalize_okx_observer(envelope: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(envelope, dict):
        raise PrivateRealityError('OKX observer envelope must be an object')
    if envelope.get('externalFinancialWriteAttempted') not in (False, None):
        raise PrivateRealityError('OKX observer must not claim an external write')
    calls = envelope.get('calls') or {}
    config_rows = _call_data(calls.get('config') or calls.get('account_get_config'))
    permission_read_only = False
    if isinstance(config_rows, list) and config_rows:
        perm = str((config_rows[0] or {}).get('perm') or '').lower()
        permission_read_only = 'read' in perm and 'trade' not in perm and 'withdraw' not in perm

    balance_rows = _call_data(calls.get('balance') or calls.get('account_get_balance'))
    balances: list[dict[str, str]] = []
    if isinstance(balance_rows, list):
        for account in balance_rows:
            if not isinstance(account, dict):
                continue
            for row in account.get('details') or []:
                if not isinstance(row, dict):
                    continue
                asset = str(row.get('ccy') or '').strip()
                if not asset:
                    continue
                available = _d(row.get('availBal', row.get('cashBal', '0')), f'{asset}.availBal')
                total = _d(row.get('eq', row.get('cashBal', '0')), f'{asset}.eq')
                locked = format(Decimal(total) - Decimal(available), 'f')
                balances.append({'asset': asset, 'available': available, 'locked': locked, 'total': total})

    position_rows = _call_data(calls.get('positions') or calls.get('account_get_positions'))
    positions = []
    if isinstance(position_rows, list):
        for r in position_rows:
            if not isinstance(r, dict):
                continue
            positions.append({
                'instrumentId': r.get('instId'),
                'positionId': r.get('posId'),
                'side': r.get('posSide'),
                'quantity': _d(r.get('pos', '0'), 'okx.position.pos'),
                'avgPx': _d(r.get('avgPx', '0'), 'okx.position.avgPx'),
                'markPx': _d(r.get('markPx', '0'), 'okx.position.markPx'),
                'venueTimestampMs': r.get('uTime'),
            })

    open_rows = _call_data(calls.get('openOrders') or calls.get('swap_get_orders'))
    fill_rows = _call_data(calls.get('fills') or calls.get('swap_get_fills'))
    open_orders = _normalize_okx_orders(open_rows if isinstance(open_rows, list) else [])
    fills = _normalize_okx_fills(fill_rows if isinstance(fill_rows, list) else [])

    return {
        'schemaVersion': 1,
        'kind': 'ordivon.market-capital.private-reality-snapshot',
        'venue': 'OKX',
        'product': 'ACCOUNT',
        'sourceAuthority': 'OKX_PRIVATE_GET',
        'sourceStatus': envelope.get('status'),
        'permissionStanding': 'READ_ONLY_VERIFIED' if permission_read_only else 'NOT_VERIFIED',
        'balances': sorted(balances, key=lambda x: x['asset']),
        'positions': positions,
        'openOrders': open_orders,
        'orderHistory': [],
        'fills': fills,
        'externalFinancialWriteAttempted': False,
    }


def _normalize_okx_orders(rows: Iterable[Any]) -> list[dict[str, Any]]:
    out=[]
    for r in rows:
        if not isinstance(r,dict): continue
        out.append({
            'venueOrderId': r.get('ordId'),
            'clientOrderId': r.get('clOrdId'),
            'instrumentId': r.get('instId'),
            'side': r.get('side'),
            'orderType': r.get('ordType'),
            'timeInForce': None,
            'status': r.get('state'),
            'originalQty': _d(r.get('sz','0'),'okx.order.sz'),
            'executedQty': _d(r.get('accFillSz','0'),'okx.order.accFillSz'),
            'price': _d(r.get('px','0'),'okx.order.px'),
            'venueTimestampMs': r.get('uTime') or r.get('cTime'),
        })
    return out


def _normalize_okx_fills(rows: Iterable[Any]) -> list[dict[str, Any]]:
    out=[]
    for r in rows:
        if not isinstance(r,dict): continue
        out.append({
            'venueTradeId': r.get('tradeId'),
            'venueOrderId': r.get('ordId'),
            'instrumentId': r.get('instId'),
            'qty': _d(r.get('fillSz','0'),'okx.fill.fillSz'),
            'price': _d(r.get('fillPx','0'),'okx.fill.fillPx'),
            'commission': _d(r.get('fee','0'),'okx.fill.fee'),
            'commissionAsset': r.get('feeCcy'),
            'venueTimestampMs': r.get('fillTime') or r.get('ts'),
        })
    return out
