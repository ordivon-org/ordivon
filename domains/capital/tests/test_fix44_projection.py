from __future__ import annotations

from copy import deepcopy

import pytest

from ordivon_capital.market.fix44_projection import (
    Fix44ProjectionError,
    project_document,
    project_new_order_single,
)


def test_local_projection_matches_frozen_quickfix_field_sequence():
    row = project_new_order_single(
        seq=1,
        sender_comp_id="ORDIVON",
        cl_ord_id="MECH-OKX-BTC",
        symbol="BTC-USDT",
        side="BUY",
        order_qty="0.00012959",
        time_in_force="IOC",
        ex_destination="OKX",
        transact_time_utc="2026-09-20T18:52:07Z",
    )
    expected = (
        "8=FIX.4.4\x0135=D\x0134=1\x0149=ORDIVON\x01"
        "52=20260920-18:52:07.000\x0156=OKX_QUALIFICATION\x01"
        "11=MECH-OKX-BTC\x0138=0.00012959\x0140=1\x0154=1\x01"
        "55=BTC-USDT\x0159=3\x0160=20260920-18:52:07.000\x01100=OKX\x01"
    )
    assert row["raw"] == expected


@pytest.mark.parametrize(
    ("side", "tif", "side_code", "tif_code"),
    [
        ("BUY", "DAY", "1", "0"),
        ("BUY", "GTC", "1", "1"),
        ("BUY", "IOC", "1", "3"),
        ("SELL", "DAY", "2", "0"),
        ("SELL", "GTC", "2", "1"),
        ("SELL", "IOC", "2", "3"),
    ],
)
def test_side_and_tif_mapping(side, tif, side_code, tif_code):
    row = project_new_order_single(
        seq=7,
        sender_comp_id="ORDIVON",
        cl_ord_id="X-7",
        symbol="AAPL",
        side=side,
        order_qty="12.3400",
        time_in_force=tif,
        ex_destination="XNAS",
        transact_time_utc="2026-09-20T18:52:07.987654Z",
    )
    assert row["side"] == side_code
    assert row["timeInForce"] == tif_code
    assert row["orderQty"] == "12.3400"
    assert "52=20260920-18:52:07.987\x01" in row["raw"]
    assert "60=20260920-18:52:07.987\x01" in row["raw"]


def _document():
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.fix44-projection-input",
        "purpose": "MECHANICS_ONLY_NON_ECONOMIC",
        "sourceEvidenceSha256": "a" * 64,
        "transactTimeUtc": "2026-09-20T18:52:07Z",
        "senderCompId": "ORDIVON_SHADOW",
        "networkSessionEnabled": False,
        "externalFinancialWritesAllowed": False,
        "intents": [
            {
                "clOrdId": "A",
                "symbol": "BTC-USDT",
                "exDestination": "OKX",
                "side": "BUY",
                "orderQty": "0.0040",
                "ordType": "MARKET",
                "timeInForce": "IOC",
            }
        ],
    }


def test_document_declares_sessionless_not_complete_wire_frame():
    result = project_document(_document())
    assert result["standing"] == "PASS_BOUNDED_LOCAL_FIX44_TAGVALUE_PROJECTION"
    assert result["projectionImplementation"] == "LOCAL_BOUNDED_FIX44_TAGVALUE_PROJECTOR"
    assert result["wireFrameComplete"] is False
    assert result["bodyLengthAndChecksumPresent"] is False
    assert result["quickfixDifferentialReference"]["byteExactMatches"] == 120
    assert result["quickfixDifferentialReference"]["mismatches"] == 0


@pytest.mark.parametrize(
    ("mutator", "match"),
    [
        (lambda d: d.__setitem__("networkSessionEnabled", True), "sessionless"),
        (lambda d: d.__setitem__("externalFinancialWritesAllowed", True), "external writes"),
        (lambda d: d["intents"][0].__setitem__("ordType", "LIMIT"), "MARKET"),
        (lambda d: d["intents"][0].__setitem__("side", "SHORT"), "BUY or SELL"),
        (lambda d: d["intents"][0].__setitem__("timeInForce", "FOK"), "DAY, GTC, or IOC"),
        (lambda d: d["intents"][0].__setitem__("orderQty", "0"), "positive"),
    ],
)
def test_out_of_contract_inputs_fail_closed(mutator, match):
    doc = deepcopy(_document())
    mutator(doc)
    with pytest.raises(Fix44ProjectionError, match=match):
        project_document(doc)
