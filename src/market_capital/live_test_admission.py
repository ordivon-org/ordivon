from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


class LiveTestAdmissionError(ValueError):
    pass


def _dec(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise LiveTestAdmissionError(f'invalid decimal: {value!r}') from exc


def evaluate_live_test_account(
    *,
    reality: dict[str, Any],
    quote_asset: str,
    permission: dict[str, Any],
    clock_passed: bool,
    reconciliation_healthy: bool,
    max_quote_balance: str = '1',
) -> dict[str, Any]:
    venue=str(reality.get('venue') or '').upper()
    reasons: list[str]=[]
    if venue not in {'OKX','BINANCE'}:
        reasons.append('unsupported-venue')
    if reality.get('permissionStanding') != 'READ_ONLY_VERIFIED':
        reasons.append('readonly-reality-not-verified')
    if reality.get('externalFinancialWriteAttempted') is not False:
        reasons.append('reality-not-readonly')
    if not clock_passed:
        reasons.append('clock-gate-not-passed')
    if not reconciliation_healthy:
        reasons.append('reconciliation-not-healthy')

    if permission.get('trade') is not True:
        reasons.append('trade-permission-missing')
    if permission.get('withdraw') is not False:
        reasons.append('withdraw-permission-not-proven-absent')
    if permission.get('transfer') not in (False, None):
        reasons.append('transfer-permission-not-proven-absent')

    positions=[p for p in (reality.get('positions') or []) if _dec(p.get('quantity','0')) != 0]
    if positions:
        reasons.append('nonzero-position-present')
    if reality.get('openOrders'):
        reasons.append('open-order-present')

    max_quote=_dec(max_quote_balance)
    quote_total=Decimal('0')
    nonquote_nonzero=[]
    for b in reality.get('balances') or []:
        asset=str(b.get('asset') or '')
        total=_dec(b.get('total','0'))
        if total == 0:
            continue
        if asset == quote_asset:
            quote_total += total
        else:
            nonquote_nonzero.append(asset)
    if nonquote_nonzero:
        reasons.append('nonquote-balance-present:' + ','.join(sorted(nonquote_nonzero)))
    if quote_total > max_quote:
        reasons.append('quote-balance-exceeds-test-threshold')

    admitted=not reasons
    return {
        'schemaVersion':1,
        'kind':'ordivon.market-capital.live-test-account-admission',
        'venue':venue,
        'standing':'ADMITTED_EMPTY_LIVE_TEST_ACCOUNT' if admitted else 'BLOCKED',
        'orderSubmissionAllowed':admitted,
        'productionTradingAuthorized':False,
        'withdrawalAuthorized':False,
        'transferAuthorized':False,
        'quoteAsset':quote_asset,
        'observedQuoteBalance':format(quote_total,'f'),
        'maxQuoteBalance':format(max_quote,'f'),
        'nonquoteNonzeroAssets':sorted(nonquote_nonzero),
        'blockingReasons':reasons,
    }
