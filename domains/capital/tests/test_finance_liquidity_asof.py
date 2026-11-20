"""Natural cross-source research consumer counterexamples, no downloaded market data."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/research/finance_liquidity_asof.py"
spec = importlib.util.spec_from_file_location("finance_liquidity_asof_test", SOURCE)
assert spec is not None and spec.loader is not None
import sys

m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)

H41_VALUES = {
    "reserveSupply": 6793431,
    "reserveAbsorption": 3791641,
    "bankReserves": 3001790,
    "treasuryGeneralAccount": 892310,
    "reverseRepo": 317043,
}
DTS_NUMBERS = (921222, 22093, 51006, 892310)


def _h41(*, release="November 19, 2026", observed="Nov 18, 2026", values=None, footnote=" 12"):
    values = dict(H41_VALUES if values is None else values)
    rows = [
        ("t1", "30", "Total factors supplying reserve funds", "reserveSupply"),
        (
            "t2",
            "14",
            "Total factors, other than reserve balances, absorbing reserve funds",
            "reserveAbsorption",
        ),
        ("t2", "16", "Reserve balances with Federal Reserve Banks", "bankReserves"),
        ("t2", "8", "U.S. Treasury, General Account", "treasuryGeneralAccount"),
        ("t2", "2", "Reverse repurchase agreements" + footnote, "reverseRepo"),
    ]
    body = "".join(
        f'<tr><td id="{tab}r{n}c1">{label}</td><td id="{tab}r{n}c5">{values[key]:,}</td></tr>'
        for tab, n, label, key in rows
    )
    return (
        f"<html><body>Release Date: {release}"
        f'<table><tr><th id="t2h1c3">Wednesday {observed}</th></tr>'
        f"{body}</table></body></html>"
    ).encode()


def _dts(*, day="2026-11-18", amounts=DTS_NUMBERS):
    rows = [
        {
            "record_date": day,
            "account_type": label,
            "open_today_bal": str(value),
            "close_today_bal": "null",
        }
        for label, value in zip(m.DTS_ROWS.values(), amounts, strict=True)
    ]
    return json.dumps({"data": rows, "meta": {"count": 4}}).encode()


def _sofr(*, update_future=False, revise=False):
    rows = [
        "Effective Date,Rate Type,Rate (%),1st Percentile (%),99th Percentile (%),Volume ($Billions),Revision Indicator (Y/N)",
        "11/16/2026,SOFR,3.93,3.91,4.00,3000,",
        f"11/17/2026,SOFR,3.92,3.90,4.02,3173,{'Y' if revise else ''}",
        "11/18/2026,SOFR,3.90,3.88,4.01,3134,",
        f"11/19/2026,SOFR,{'8.99' if update_future else '3.91'},3.88,9.99,3400,",
    ]
    return ("\n".join(rows) + "\n").encode()


def _parse():
    h = m.parse_h41(_h41(), file_label="h41-20261119.html")
    d = m.parse_dts(_dts())
    s = m.parse_sofr(_sofr())
    return h, d, s


def test_real_official_figure_accounting_identity_and_units():
    h, d, _ = _parse()
    assert h.observed_date.isoformat() == "2026-11-18"
    assert h.release_date.isoformat() == "2026-11-19"
    assert h.values["reserveSupply"] - h.values["reserveAbsorption"] == 3001790
    assert h.values["treasuryGeneralAccount"] == d.closing == 892310
    assert d.rounding_residual == -1


def test_h41_closing_of_wednesday_is_not_weekly_average():
    h, _, _ = _parse()
    assert h.values["bankReserves"] == 3001790
    # Synthetic row includes only the c5 Wed stock; no average c2 is supplied.
    assert h.values["treasuryGeneralAccount"] == 892310


def test_h41_false_accounting_or_label_or_release_name_rejected():
    incorrect = dict(H41_VALUES, bankReserves=3001789)
    with pytest.raises(ValueError, match="conservation"):
        m.parse_h41(_h41(values=incorrect), file_label="h41-20261119.html")
    with pytest.raises(ValueError, match="source row"):
        m.parse_h41(
            _h41().replace(b"Reserve balances with Federal Reserve Banks", b"Cash"),
            file_label="h41-20261119.html",
        )
    with pytest.raises(ValueError, match="date content disagreement"):
        m.parse_h41(_h41(), file_label="h41-20261112.html")


def test_dts_2022_schema_closing_is_in_account_type_row_not_close_today_bal():
    r = json.loads(_dts())
    assert r["data"][3]["close_today_bal"] == "null"
    assert m.parse_dts(_dts()).closing == 892310
    r["data"][3]["close_today_bal"] = "892310"
    with pytest.raises(ValueError, match="post-2022"):
        m.parse_dts(json.dumps(r).encode())


def test_dts_larger_than_rounding_disagreement_is_not_accepted():
    with pytest.raises(ValueError, match="conservation"):
        m.parse_dts(_dts(amounts=(921222, 22093, 51006, 892999)))
    r = json.loads(_dts())
    r["data"][2]["open_today_bal"] = "null"
    with pytest.raises(ValueError, match="not default to zero"):
        m.parse_dts(json.dumps(r).encode())


def test_sofr_revised_or_future_rows_do_not_change_old_state():
    h, d, s = _parse()
    before = m.asof_snapshot(
        when=datetime.fromisoformat("2026-11-19T21:00:00+00:00"),
        h41=[h],
        dts=[d],
        sofr=s,
        sofr_sha256="synthetic",
    )
    assert before["sofr"]["effectiveDate"] == "2026-11-17"
    modified = m.parse_sofr(_sofr(update_future=True))
    after = m.asof_snapshot(
        when=datetime.fromisoformat("2026-11-19T21:00:00+00:00"),
        h41=[h],
        dts=[d],
        sofr=modified,
        sofr_sha256="synthetic",
    )
    assert after["sofr"]["ratePct"] == before["sofr"]["ratePct"] == "3.92"
    with pytest.raises(ValueError, match="revised"):
        m.parse_sofr(_sofr(revise=True))


def test_thursday_stock_close_cannot_consume_later_h41_release():
    h, d, s = _parse()
    before = m.asof_snapshot(
        when=datetime.fromisoformat("2026-11-19T21:00:00+00:00"),
        h41=[h],
        dts=[d],
        sofr=s,
        sofr_sha256="synthetic",
    )
    after = m.asof_snapshot(
        when=datetime.fromisoformat("2026-11-19T22:00:00+00:00"),
        h41=[h],
        dts=[d],
        sofr=s,
        sofr_sha256="synthetic",
    )
    assert before["h41"] is None
    assert after["h41"]["releasedOn"] == "2026-11-19"
    # At both instants the delayed API observation is NOT eligible.
    assert before["dts"] is after["dts"] is None
    assert after["capitalAndTradingAuthority"] is False


def test_cross_source_same_day_only_after_conservative_treasury_availability():
    h, d, s = _parse()
    after = m.asof_snapshot(
        when=datetime.fromisoformat("2026-11-20T15:00:00+00:00"),
        h41=[h],
        dts=[d],
        sofr=s,
        sofr_sha256="synthetic",
    )
    assert after["crossSourceTga"] == "MATCHED_SAME_DAY_MILLION_USD"
    assert after["sofr"]["effectiveDate"] == "2026-11-18"
    assert after["compositeLiquidityScore"] is None


def test_cross_source_disagreement_is_not_collapsed_into_one_authority():
    h, _, s = _parse()
    # One-million-dollar rounded mismatch still passes individual DTS
    # conservation (+/- 2 million) but MUST NOT pass cross-source equality.
    d = m.parse_dts(_dts(amounts=(921222, 22093, 51006, 892311)))
    result = m.asof_snapshot(
        when=datetime.fromisoformat("2026-11-20T15:00:00+00:00"),
        h41=[h],
        dts=[d],
        sofr=s,
        sofr_sha256="synthetic",
    )
    assert result["crossSourceTga"] == "CONFLICT_DO_NOT_COMBINE"
    assert result["compositeLiquidityScore"] is None


def test_dst_release_clock_uses_new_york_not_fixed_utc_offset():
    h = m.parse_h41(
        _h41(release="July 16, 2026", observed="Jul 15, 2026"), file_label="h41-20260716.html"
    )
    s = m.parse_sofr(_sofr())
    # No July SOFR record; that's fine, only test the July archive boundary.
    before = m.asof_snapshot(
        when=datetime.fromisoformat("2026-07-16T20:00:00+00:00"),
        h41=[h],
        dts=[],
        sofr=s,
        sofr_sha256="synthetic",
    )
    after = m.asof_snapshot(
        when=datetime.fromisoformat("2026-07-16T20:31:00+00:00"),
        h41=[h],
        dts=[],
        sofr=s,
        sofr_sha256="synthetic",
    )
    assert before["h41"] is None
    assert after["h41"]["releasedOn"] == "2026-07-16"


def test_naive_asof_and_duplicate_h41_are_rejected():
    h, d, s = _parse()
    with pytest.raises(ValueError, match="timezone aware"):
        m.asof_snapshot(
            when=datetime(2026, 11, 20, 10), h41=[h], dts=[d], sofr=s, sofr_sha256="synthetic"
        )
    with pytest.raises(ValueError, match="duplicate Treasury source record date"):
        m.run(
            raw_h41={"h41-20261119.html": _h41()},
            raw_dts=[_dts(), _dts()],
            raw_sofr=_sofr(),
            at=["2026-11-20T15:00:00+00:00"],
        )


def test_fiscal_and_h41_observation_days_are_not_implicitly_joined():
    h, d, s = _parse()
    old_dts = m.parse_dts(_dts(day="2026-11-04"))
    result = m.asof_snapshot(
        when=datetime.fromisoformat("2026-11-20T15:00:00+00:00"),
        h41=[h],
        dts=[old_dts],
        sofr=s,
        sofr_sha256="synthetic",
    )
    assert result["crossSourceTga"] == "DIFFERENT_OBSERVATION_DAY"
    assert result["dts"]["recordDate"] == "2026-11-04"
    assert result["h41"]["observedOn"] == "2026-11-18"
