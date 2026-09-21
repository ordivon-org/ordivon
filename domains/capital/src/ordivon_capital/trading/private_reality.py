from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal, InvalidOperation
from typing import Any


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
        'schemaVersion': 2,
        'kind': 'ordivon.capital.trading.private-reality-snapshot',
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
        'coverage': {
            'accountComplete': _call_data(calls.get('account_get_account')) is not None,
            'openOrdersComplete': any(isinstance(k,str) and k.endswith(':account_open_orders') and isinstance(v,dict) and v.get('ok') is True for k,v in calls.items()),
            'orderHistoryComplete': any(isinstance(k,str) and k.endswith(':account_all_orders') and isinstance(v,dict) and v.get('ok') is True for k,v in calls.items()),
            'fillsComplete': any(isinstance(k,str) and k.endswith(':account_my_trades') and isinstance(v,dict) and v.get('ok') is True for k,v in calls.items()),
        },
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
        'schemaVersion': 2,
        'kind': 'ordivon.capital.trading.private-reality-snapshot',
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
        'coverage': {
            'accountComplete': isinstance(balance_rows,list),
            'openOrdersComplete': isinstance(open_rows,list),
            'orderHistoryComplete': False,
            'fillsComplete': isinstance(fill_rows,list),
        },
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


def _sdk_data(call: Any) -> Any:
    if not isinstance(call, dict) or call.get('ok') is not True:
        return None
    return call.get('data')


def _as_rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [r for r in value if isinstance(r, dict)]
    if isinstance(value, dict):
        if isinstance(value.get('actual_instance'), list):
            return [r for r in value['actual_instance'] if isinstance(r, dict)]
        return [value]
    return []


def normalize_binance_usdm_observer(envelope: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(envelope, dict):
        raise PrivateRealityError('Binance USD-M observer envelope must be an object')
    if envelope.get('externalFinancialWriteAttempted') is not False:
        raise PrivateRealityError('Binance USD-M observer must prove externalFinancialWriteAttempted=false')

    gate = envelope.get('permissionGate') or {}
    permission_safe = gate.get('safe') is True
    calls = envelope.get('calls') or {}

    account = _sdk_data(calls.get('account_information_v3'))
    balance_rows = _as_rows(_sdk_data(calls.get('futures_account_balance_v3')))
    config = _sdk_data(calls.get('futures_account_configuration'))
    multi_assets = _sdk_data(calls.get('get_current_multi_assets_mode'))
    position_mode = _sdk_data(calls.get('get_current_position_mode'))
    bracket_data = _sdk_data(calls.get('notional_and_leverage_brackets'))
    adl_data = _sdk_data(calls.get('position_adl_quantile_estimation'))
    position_rows = _as_rows(_sdk_data(calls.get('position_information_v3')))
    order_rows = _as_rows(_sdk_data(calls.get('current_all_open_orders')))
    trade_rows = _as_rows(_sdk_data(calls.get('account_trade_list')))

    balances: list[dict[str, Any]] = []
    for row in balance_rows:
        asset = str(row.get('asset') or '').strip()
        if not asset:
            continue
        total = _d(row.get('balance', '0'), f'{asset}.balance')
        available = _d(row.get('available_balance', '0'), f'{asset}.available_balance')
        locked = format(Decimal(total) - Decimal(available), 'f')
        balances.append({
            'asset': asset,
            'available': available,
            'locked': locked,
            'total': total,
            'crossWalletBalance': _d(row.get('cross_wallet_balance', '0'), f'{asset}.cross_wallet_balance'),
            'crossUnPnl': _d(row.get('cross_un_pnl', '0'), f'{asset}.cross_un_pnl'),
            'marginAvailable': row.get('margin_available'),
            'venueTimestampMs': row.get('update_time'),
        })

    positions: list[dict[str, Any]] = []
    for row in position_rows:
        symbol = str(row.get('symbol') or '').strip()
        if not symbol:
            continue
        qty = _d(row.get('position_amt', '0'), f'{symbol}.position_amt')
        positions.append({
            'instrumentId': symbol,
            'positionSide': row.get('position_side'),
            'quantity': qty,
            'entryPx': _d(row.get('entry_price', '0'), f'{symbol}.entry_price'),
            'breakEvenPx': _d(row.get('break_even_price', '0'), f'{symbol}.break_even_price'),
            'markPx': _d(row.get('mark_price', '0'), f'{symbol}.mark_price'),
            'unrealizedPnl': _d(row.get('un_realized_profit', '0'), f'{symbol}.un_realized_profit'),
            'liquidationPx': _d(row.get('liquidation_price', '0'), f'{symbol}.liquidation_price'),
            'notional': _d(row.get('notional', '0'), f'{symbol}.notional'),
            'marginAsset': row.get('margin_asset'),
            'initialMargin': _d(row.get('initial_margin', '0'), f'{symbol}.initial_margin'),
            'maintenanceMargin': _d(row.get('maint_margin', '0'), f'{symbol}.maint_margin'),
            'positionInitialMargin': _d(row.get('position_initial_margin', '0'), f'{symbol}.position_initial_margin'),
            'openOrderInitialMargin': _d(row.get('open_order_initial_margin', '0'), f'{symbol}.open_order_initial_margin'),
            'adl': row.get('adl'),
            'venueTimestampMs': row.get('update_time'),
        })

    open_orders = []
    for row in order_rows:
        open_orders.append({
            'venueOrderId': str(row.get('order_id')) if row.get('order_id') is not None else None,
            'clientOrderId': row.get('client_order_id'),
            'instrumentId': row.get('symbol'),
            'side': row.get('side'),
            'positionSide': row.get('position_side'),
            'orderType': row.get('type'),
            'timeInForce': row.get('time_in_force'),
            'status': row.get('status'),
            'reduceOnly': row.get('reduce_only'),
            'closePosition': row.get('close_position'),
            'originalQty': _d(row.get('orig_qty', '0'), 'binance_usdm.orig_qty'),
            'executedQty': _d(row.get('executed_qty', '0'), 'binance_usdm.executed_qty'),
            'price': _d(row.get('price', '0'), 'binance_usdm.price'),
            'venueTimestampMs': row.get('update_time') or row.get('time'),
        })

    fills = []
    for row in trade_rows:
        fills.append({
            'venueTradeId': str(row.get('id')) if row.get('id') is not None else None,
            'venueOrderId': str(row.get('order_id')) if row.get('order_id') is not None else None,
            'instrumentId': row.get('symbol'),
            'side': row.get('side'),
            'positionSide': row.get('position_side'),
            'qty': _d(row.get('qty', '0'), 'binance_usdm.trade.qty'),
            'price': _d(row.get('price', '0'), 'binance_usdm.trade.price'),
            'commission': _d(row.get('commission', '0'), 'binance_usdm.trade.commission'),
            'commissionAsset': row.get('commission_asset'),
            'realizedPnl': _d(row.get('realized_pnl', '0'), 'binance_usdm.trade.realized_pnl'),
            'venueTimestampMs': row.get('time'),
        })

    return {
        'schemaVersion': 2,
        'kind': 'ordivon.capital.trading.private-reality-snapshot',
        'venue': 'BINANCE',
        'product': 'USDⓈ-M_FUTURES',
        'sourceAuthority': 'BINANCE_USDM_USER_DATA_GET_ONLY',
        'sourceStatus': envelope.get('standing'),
        'permissionStanding': 'READ_ONLY_VERIFIED' if permission_safe else 'NOT_VERIFIED',
        'balances': sorted(balances, key=lambda x: x['asset']),
        'positions': positions,
        'openOrders': open_orders,
        'orderHistory': [],
        'fills': fills,
        'coverage': {
            'accountComplete': isinstance(account, dict),
            'balancesComplete': _sdk_data(calls.get('futures_account_balance_v3')) is not None,
            'positionsComplete': _sdk_data(calls.get('position_information_v3')) is not None,
            'openOrdersComplete': _sdk_data(calls.get('current_all_open_orders')) is not None,
            'fillsComplete': _sdk_data(calls.get('account_trade_list')) is not None,
            'leverageBracketComplete': bracket_data is not None,
            'adlComplete': adl_data is not None,
        },
        'accountRisk': {
            'totalInitialMargin': _d((account or {}).get('total_initial_margin', '0'), 'account.total_initial_margin') if isinstance(account, dict) else None,
            'totalMaintenanceMargin': _d((account or {}).get('total_maint_margin', '0'), 'account.total_maint_margin') if isinstance(account, dict) else None,
            'totalWalletBalance': _d((account or {}).get('total_wallet_balance', '0'), 'account.total_wallet_balance') if isinstance(account, dict) else None,
            'totalUnrealizedPnl': _d((account or {}).get('total_unrealized_profit', '0'), 'account.total_unrealized_profit') if isinstance(account, dict) else None,
            'totalMarginBalance': _d((account or {}).get('total_margin_balance', '0'), 'account.total_margin_balance') if isinstance(account, dict) else None,
            'availableBalance': _d((account or {}).get('available_balance', '0'), 'account.available_balance') if isinstance(account, dict) else None,
        },
        'accountConfiguration': config,
        'multiAssetsMode': multi_assets,
        'positionMode': position_mode,
        'leverageBracket': bracket_data,
        'positionAdlQuantile': adl_data,
        'tradFiAgreementStanding': 'UNKNOWN_NO_READ_ONLY_STATUS_API',
        'tradeEligibilityStanding': 'NOT_INFERRED_FROM_READ_SURFACE',
        'executionAdmitted': False,
        'externalFinancialWriteAttempted': False,
    }
