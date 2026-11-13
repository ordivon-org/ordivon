import pytest

from ordivon_capital.trading.execution_reconciliation import (
    ReconciliationError,
    reconcile_fix_intent,
)

INTENT={'protocol':'FIX.4.4','msgType':'D','clOrdId':'C-1','exDestination':'BINANCE','symbol':'BTCUSDT','orderQty':'0.1'}

def reality(*, orders=None, history=None, fills=None, permission='READ_ONLY_VERIFIED', fills_complete=True):
 return {'venue':'BINANCE','permissionStanding':permission,'openOrders':orders or [],'orderHistory':history or [],'fills':fills or [],'coverage':{'fillsComplete':fills_complete},'externalFinancialWriteAttempted':False}

def order(status='NEW',executed='0',oid='1'):
 return {'venueOrderId':oid,'clientOrderId':'C-1','instrumentId':'BTCUSDT','status':status,'originalQty':'0.1','executedQty':executed,'price':'50000'}

def fill(oid='1'):
 return {'venueTradeId':'7','venueOrderId':oid,'instrumentId':'BTCUSDT','qty':'0.1','price':'50010'}

def test_fill_consumes_effect_authority():
 x=reconcile_fix_intent(intent=INTENT,reality=reality(history=[order('FILLED','0.1')],fills=[fill()]))
 assert x['standing']=='POSITIVE_EXECUTION'; assert x['reservationResolution']=='POST_PENDING_TRANSFER'
 assert x['fixLifecycle']['execType']=='F'; assert x['fixLifecycle']['ordStatus']=='2'

def test_open_order_retains_effect_authority():
 x=reconcile_fix_intent(intent=INTENT,reality=reality(orders=[order('NEW','0')]))
 assert x['standing']=='PARTIAL_OPEN'; assert x['reservationResolution']=='NO_MUTATION'
 assert x['fixLifecycle']['ordStatus']=='0'

def test_terminal_zero_fill_releases_only_with_complete_fill_query():
 x=reconcile_fix_intent(intent=INTENT,reality=reality(history=[order('CANCELED','0')],fills_complete=True))
 assert x['standing']=='RECONCILED_ZERO_FILL_TERMINAL'; assert x['reservationResolution']=='VOID_PENDING_TRANSFER'
 y=reconcile_fix_intent(intent=INTENT,reality=reality(history=[order('CANCELED','0')],fills_complete=False))
 assert y['reservationResolution']=='NO_MUTATION'

def test_absence_from_snapshot_is_unknown_not_no_effect():
 x=reconcile_fix_intent(intent=INTENT,reality=reality())
 assert x['standing']=='UNKNOWN'; assert x['reservationResolution']=='NO_MUTATION'

def test_exact_authoritative_negative_lookup_can_release():
 exact={'venue':'BINANCE','clientOrderId':'C-1','authoritative':True,'querySucceeded':True,'orderFound':False,'fillFound':False}
 x=reconcile_fix_intent(intent=INTENT,reality=reality(),exact_lookup=exact)
 assert x['standing']=='PROVEN_NO_EFFECT'; assert x['reservationResolution']=='VOID_PENDING_TRANSFER'

def test_unverified_private_read_permission_retains():
 x=reconcile_fix_intent(intent=INTENT,reality=reality(permission='NOT_VERIFIED'))
 assert x['standing']=='UNKNOWN'; assert x['reservationResolution']=='NO_MUTATION'


def test_partial_fill_cannot_consume_entire_reservation():
    observed = dict(fill())
    observed["qty"] = "0.04"
    x = reconcile_fix_intent(
        intent=INTENT,
        reality=reality(orders=[order("PARTIALLY_FILLED", "0.04")], fills=[observed]),
    )
    assert x["standing"] == "PARTIAL_EXECUTION_UNSETTLED"
    assert x["reservationResolution"] == "NO_MUTATION"
    assert x["matchedFillCount"] == 1
    assert x["fixLifecycle"]["cumQty"] == "0.04"
    assert x["fixLifecycle"]["leavesQty"] == "0.06"


def test_cancel_after_partial_fill_is_not_zero_fill_cancellation():
    x = reconcile_fix_intent(
        intent=INTENT, reality=reality(
            history=[order("CANCELED", "0.04")],
            fills=[dict(fill(), qty="0.04")],
        ),
    )
    assert x["standing"] == "PARTIAL_EXECUTION_UNSETTLED"
    assert x["reservationResolution"] == "NO_MUTATION"
    assert x["fixLifecycle"]["ordStatus"] == "4"


def test_filled_with_mismatched_intent_quantity_cannot_settle_full_reservation():
    modified = dict(INTENT, orderQty="0.2")
    x = reconcile_fix_intent(
        intent=modified, reality=reality(history=[order("FILLED", "0.1")], fills=[fill()]),
    )
    assert x["standing"] == "CONTRADICTORY"
    assert x["reservationResolution"] == "NO_MUTATION"


def test_filled_with_incomplete_reported_quantity_cannot_settle():
    x = reconcile_fix_intent(
        intent=INTENT, reality=reality(history=[order("FILLED", "0.04")],
                                      fills=[dict(fill(), qty="0.04")]),
    )
    assert x["standing"] == "CONTRADICTORY"
    assert x["reservationResolution"] == "NO_MUTATION"


def test_filled_with_conflicting_complete_fill_sum_cannot_settle():
    x = reconcile_fix_intent(
        intent=INTENT, reality=reality(
            history=[order("FILLED", "0.1")], fills=[dict(fill(), qty="0.04")],
            fills_complete=True,
        ),
    )
    assert x["standing"] == "CONTRADICTORY"
    assert x["reservationResolution"] == "NO_MUTATION"


def test_filled_with_two_complete_deduplicable_slices_settles():
    a = dict(fill(), qty="0.04")
    b = dict(fill(), venueTradeId="8", qty="0.06")
    x = reconcile_fix_intent(
        intent=INTENT, reality=reality(history=[order("FILLED", "0.1")], fills=[a, b]),
    )
    assert x["standing"] == "POSITIVE_EXECUTION"
    assert x["reservationResolution"] == "POST_PENDING_TRANSFER"
    assert x["matchedFillCount"] == 2


def test_reported_full_execution_without_fills_is_not_settlement_proof():
    x = reconcile_fix_intent(
        intent=INTENT,
        reality=reality(history=[order("FILLED", "0.1")], fills_complete=False),
    )
    assert x["standing"] == "AMBIGUOUS"
    assert x["reservationResolution"] == "NO_MUTATION"


def test_nonfinite_quantity_must_not_mutate_money():
    with pytest.raises(ReconciliationError, match="quantity"):
        reconcile_fix_intent(intent=INTENT, reality=reality(history=[order("FILLED", "NaN")]))


def test_reused_client_order_id_with_distinct_venue_order_ids_cannot_settle():
    x = reconcile_fix_intent(
        intent=INTENT,
        reality=reality(history=[order("FILLED", "0.1", oid="first"),
                                 order("FILLED", "0.1", oid="second")]),
    )
    assert x["standing"] == "AMBIGUOUS"
    assert x["reservationResolution"] == "NO_MUTATION"


def test_duplicate_venue_trade_ids_are_not_twice_counted_as_full_fill():
    first = dict(fill(), qty="0.05")
    second = dict(first)
    x = reconcile_fix_intent(
        intent=INTENT, reality=reality(history=[order("FILLED", "0.1")],
                                      fills=[first, second]),
    )
    assert x["standing"] == "CONTRADICTORY"
    assert x["reservationResolution"] == "NO_MUTATION"
