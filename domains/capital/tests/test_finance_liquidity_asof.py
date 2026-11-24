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
    "reverseRepoForeignOfficial": 316712,
    "reverseRepoOthers": 331,
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
        ("t2", "3", "Foreign official and international accounts", "reverseRepoForeignOfficial"),
        ("t2", "4", "Others", "reverseRepoOthers"),
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


def test_reverse_repo_total_is_not_misidentified_as_only_on_rrp():
    h, _, _ = _parse()
    assert h.values["reverseRepo"] == 317043
    assert h.values["reverseRepoForeignOfficial"] == 316712
    assert h.values["reverseRepoOthers"] == 331
    assert h.values["reverseRepo"] == (
        h.values["reverseRepoForeignOfficial"] + h.values["reverseRepoOthers"]
    )
    wrong = dict(H41_VALUES, reverseRepoForeignOfficial=316711)
    with pytest.raises(ValueError, match="subdivision mismatch"):
        m.parse_h41(_h41(values=wrong), file_label="h41-20261119.html")


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
    # The official DTS release for the Wednesday observation is normally
    # by 16:00 Thursday; we use a 16:30 ET scheduled buffer.
    assert before["dts"] is None
    assert after["dts"]["recordDate"] == "2026-11-18"
    assert after["crossSourceTga"] == "MATCHED_SAME_DAY_MILLION_USD"
    assert after["capitalAndTradingAuthority"] is False


def test_cross_source_same_day_after_federal_business_release_time():
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


def test_friday_treasury_report_cannot_release_on_weekend():
    h, _, s = _parse()
    d = m.parse_dts(_dts(day="2026-11-13"))
    # Friday observation: next Federal business day Monday November 16,
    # not Sunday November 15, even if 2 calendar days have passed.
    before = m.asof_snapshot(
        when=datetime.fromisoformat("2026-11-15T22:00:00+00:00"),
        h41=[h],
        dts=[d],
        sofr=s,
        sofr_sha256="synthetic",
    )
    after = m.asof_snapshot(
        when=datetime.fromisoformat("2026-11-16T22:00:00+00:00"),
        h41=[h],
        dts=[d],
        sofr=s,
        sofr_sha256="synthetic",
    )
    assert before["dts"] is None
    assert after["dts"]["recordDate"] == "2026-11-13"


def test_veterans_day_holiday_is_not_issued_treasury_observation():
    with pytest.raises(ValueError, match="not a US federal business day"):
        m.parse_dts(_dts(day="2026-11-11"))
    h, _, s = _parse()
    d = m.parse_dts(_dts(day="2026-11-10"))
    # Wednesday 11/11 is a federal holiday; Nov10 DTS can qualify
    # only at the following Federal business day Thu Nov12 16:30 ET.
    before = m.asof_snapshot(
        when=datetime.fromisoformat("2026-11-11T22:00:00+00:00"),
        h41=[h],
        dts=[d],
        sofr=s,
        sofr_sha256="synthetic",
    )
    after = m.asof_snapshot(
        when=datetime.fromisoformat("2026-11-12T22:00:00+00:00"),
        h41=[h],
        dts=[d],
        sofr=s,
        sofr_sha256="synthetic",
    )
    assert before["dts"] is None
    assert after["dts"]["recordDate"] == "2026-11-10"


def test_treasury_thanksgiving_and_dst_release_boundaries():
    scheduled = m._treasury_next_scheduled_publication(
        datetime.fromisoformat("2026-11-25T12:00:00").date()
    )
    assert scheduled.isoformat() == "2026-11-27T16:30:00-05:00"
    regular = m._treasury_next_scheduled_publication(
        datetime.fromisoformat("2026-07-15T12:00:00").date()
    )
    assert regular.isoformat() == "2026-07-16T16:30:00-04:00"


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


def _dealer_inputs(*, withhold_lent=True):
    """Two real-shaped NY Fed weekly observations across three native key IDs."""
    import csv
    import io

    o = io.StringIO()
    writer = csv.writer(o)
    writer.writerow(["Key Id", "Label", "Series Break"])
    for key, (_, evidence) in m.DEALER_KEYS.items():
        writer.writerow([key, "Total - U.S. Treasury: " + evidence, "SBN2024"])
    meta = o.getvalue().encode()
    data = {}
    for key in m.DEALER_KEYS:
        previous = (
            "467271"
            if key == "PDPOSGST-TOT"
            else ("423640" if key == "PDSIOSB-UTSETTOT" else "120072")
        )
        newer = (
            "456007"
            if key == "PDPOSGST-TOT"
            else ("411760" if key == "PDSIOSB-UTSETTOT" else "*" if withhold_lent else "123465")
        )
        data[key] = json.dumps(
            {
                "pd": {
                    "timeseries": [
                        {"asofdate": "2026-11-04", "keyid": key, "value": previous},
                        {"asofdate": "2026-11-11", "keyid": key, "value": newer},
                        {"asofdate": "2026-11-18", "keyid": key, "value": "999999"},
                    ]
                }
            }
        ).encode()
    return meta, data


def test_official_dealer_observation_is_not_available_same_week():
    catalog, raw = _dealer_inputs()
    series = m.parse_dealer_sources(catalog=catalog, series=raw)
    before = m._dealer_asof(
        local=datetime.fromisoformat("2026-11-19T16:00:00-05:00"), series=series
    )
    after = m._dealer_asof(local=datetime.fromisoformat("2026-11-19T16:31:00-05:00"), series=series)
    net = "treasuryExTipsNetDealerPosition"
    assert before["weeklySeries"][net]["weekEnded"] == "2026-11-04"
    assert before["weeklySeries"][net]["valueUsdMillions"] == "467271"
    assert after["weeklySeries"][net]["weekEnded"] == "2026-11-11"
    assert after["weeklySeries"][net]["valueUsdMillions"] == "456007"
    assert after["weeklySeries"][net]["scheduledAvailableAtNewYork"] == "2026-11-19T16:30:00-05:00"
    assert after["firstPublishedVintageAttested"] is False


def test_nyfed_star_is_not_zero_or_previous_week_imputation():
    catalog, raw = _dealer_inputs()
    series = m.parse_dealer_sources(catalog=catalog, series=raw)
    snap = m._dealer_asof(local=datetime.fromisoformat("2026-11-20T10:00:00-05:00"), series=series)
    lent = snap["weeklySeries"]["treasuryExTipsSecuritiesLent"]
    assert lent["weekEnded"] == "2026-11-11"
    assert lent["availability"] == "PUBLISHED_VALUE_WITHHELD"
    assert lent["valueUsdMillions"] is None
    assert snap["weekAlignment"] == "SAME_REPORTED_WEEK"
    assert snap["weeklySeries"]["treasuryExTipsSecuritiesBorrowed"]["valueUsdMillions"] == "411760"


def test_primary_dealer_thanksgiving_federal_holiday_delays_release():
    assert (
        m._dealer_scheduled_publication(
            datetime.fromisoformat("2026-11-18T12:00:00").date()
        ).isoformat()
        == "2026-11-27T16:30:00-05:00"
    )
    catalog, raw = _dealer_inputs(withhold_lent=False)
    series = m.parse_dealer_sources(catalog=catalog, series=raw)
    thursday = m._dealer_asof(
        local=datetime.fromisoformat("2026-11-26T17:00:00-05:00"), series=series
    )
    friday = m._dealer_asof(
        local=datetime.fromisoformat("2026-11-27T16:31:00-05:00"), series=series
    )
    net = "treasuryExTipsNetDealerPosition"
    assert thursday["weeklySeries"][net]["weekEnded"] == "2026-11-11"
    assert friday["weeklySeries"][net]["weekEnded"] == "2026-11-18"


def test_wrong_dealer_catalog_break_and_key_substitution_rejected():
    catalog, raw = _dealer_inputs()
    with pytest.raises(ValueError, match="series set incomplete"):
        m.parse_dealer_sources(catalog=catalog, series={})
    invalid_catalog = catalog.replace(b"SBN2024", b"SBN2015", 1)
    with pytest.raises(ValueError, match="series break"):
        m.parse_dealer_sources(catalog=invalid_catalog, series=raw)
    fake = dict(raw)
    key = "PDPOSGST-TOT"
    data = json.loads(fake[key])
    data["pd"]["timeseries"][1]["keyid"] = "PDSOOS-UTSETTOT"
    fake[key] = json.dumps(data).encode()
    with pytest.raises(ValueError, match="weekly identity"):
        m.parse_dealer_sources(catalog=catalog, series=fake)


def test_withheld_dealer_not_a_market_research_alpha_or_capital_approval():
    catalog, raw = _dealer_inputs()
    output = m.run(
        raw_h41={"h41-20261119.html": _h41()},
        raw_dts=[_dts()],
        raw_sofr=_sofr(),
        raw_dealer_catalog=catalog,
        raw_dealer_series=raw,
        at=["2026-11-19T21:00:00+00:00", "2026-11-19T22:00:00+00:00", "2026-11-20T15:00:00+00:00"],
    )
    assert output["sourceCounts"]["dealerNativeSeries"] == 3
    assert output["standing"] == "RELEASE_CALENDAR_ALIGNED_SOURCE_HISTORY_UNATTESTED"
    assert (
        output["snapshots"][0]["dealer"]["weeklySeries"]["treasuryExTipsNetDealerPosition"][
            "weekEnded"
        ]
        == "2026-11-04"
    )
    assert (
        output["snapshots"][1]["dealer"]["weeklySeries"]["treasuryExTipsNetDealerPosition"][
            "weekEnded"
        ]
        == "2026-11-11"
    )
    assert (
        output["snapshots"][2]["dealer"]["weeklySeries"]["treasuryExTipsSecuritiesLent"][
            "valueUsdMillions"
        ]
        is None
    )
    assert all(r["capitalAndTradingAuthority"] is False for r in output["snapshots"])
    assert all(r["compositeLiquidityScore"] is None for r in output["snapshots"])


def test_no_week_yet_eligible_is_not_mislabeled_as_same_reported_week():
    catalog, raw = _dealer_inputs()
    panel = m.parse_dealer_sources(catalog=catalog, series=raw)
    state = m._dealer_asof(local=datetime.fromisoformat("2024-07-10T10:00:00-04:00"), series=panel)
    assert state["weekAlignment"] == "NO_ELIGIBLE_DEALER_WEEK"
    assert all(
        row["availability"] == "NO_WEEK_YET_RELEASE_ELIGIBLE"
        and row["weekEnded"] is None
        and row["valueUsdMillions"] is None
        for row in state["weeklySeries"].values()
    )


def test_duplicate_dealer_cli_file_is_rejected_before_file_read(monkeypatch, capsys):
    import sys

    args = [
        "finance_liquidity_asof.py",
        "--h41",
        "fake.html",
        "--dts",
        "fake.json",
        "--sofr",
        "fake.csv",
        "--at",
        "2026-11-20T15:00:00+00:00",
        "--dealer-catalog",
        "catalog.csv",
        "--dealer-series",
        "PDPOSGST-TOT.json",
        "--dealer-series",
        "PDPOSGST-TOT.json",
    ]
    monkeypatch.setattr(sys, "argv", args)
    with pytest.raises(SystemExit) as exc:
        m.main()
    assert exc.value.code == 2
    assert "duplicate dealer source ID" in capsys.readouterr().err


def test_optional_routput_integrates_without_conflating_other_sources(monkeypatch):
    from ordivon_capital.markets import rtdsm_real_output as r

    archive = r.admit_routput_rows([
        ["DATE", "ROUTPUT26M9", "ROUTPUT26M10"],
        ["2026:Q2", 24000.0, 24000.0],
        ["2026:Q3", "#N/A", 24200.0],
    ], source_sha256="b" * 64)
    monkeypatch.setattr(r, "parse_routput_archive", lambda raw, expected_sha256: archive)
    output = m.run(
        raw_h41={"h41-20261119.html": _h41()}, raw_dts=[_dts()], raw_sofr=_sofr(),
        at=["2026-11-19T17:00:00-05:00"],
        raw_routput=b"fixture", routput_sha256="b" * 64, routput_quarter="2026:Q3",
    )
    row = output["snapshots"][0]
    assert row["realOutput"]["levelRealUsdBillions"] == "24200.0"
    assert row["realOutput"]["vintageColumn"] == "ROUTPUT26M10"
    assert row["compositeLiquidityScore"] is None
    assert row["capitalAndTradingAuthority"] is False


@pytest.mark.provider_qualification
def test_actual_routput_workbook_through_existing_asof_cli(tmp_path):
    import os
    import subprocess

    path = os.environ.get("ORDIVON_FINANCE_ROUTPUT_XLSX")
    if not path:
        pytest.skip("exact original ROUTPUT workbook not supplied")
    # Macro workbook is real; the other independent inputs here are fixtures
    # and deliberately later than the two historical research decision dates.
    h41 = tmp_path / "h41-20261119.html"
    dts = tmp_path / "dts.json"
    sofr = tmp_path / "sofr.csv"
    h41.write_bytes(_h41())
    dts.write_bytes(_dts())
    sofr.write_bytes(_sofr())
    out = subprocess.run(
        [sys.executable, str(SOURCE), "--h41", str(h41), "--dts", str(dts),
         "--sofr", str(sofr), "--routput", path,
         "--routput-sha256", "ae854a7518bf3a0504e4c477344bd7ed98c4321326ed2b1952b69ffaa1a7adce",
         "--routput-quarter", "2024:Q4", "--at", "2025-02-01T00:00:00-05:00",
         "--at", "2025-03-01T00:00:00-05:00"],
        env={**os.environ, "PYTHONPATH": str(SOURCE.parents[2] / "src")},
        text=True, capture_output=True, check=True,
    )
    unknown, known = json.loads(out.stdout)["snapshots"]
    assert unknown["realOutput"]["reason"] == "MISSING_IN_ELIGIBLE_VINTAGE"
    assert known["realOutput"]["levelRealUsdBillions"] == "23530.9"
    assert known["realOutput"]["sourceBytesDigestStanding"] == "MATCHED_EXPECTED_SHA256"
    assert known["h41"] is None and known["dts"] is None and known["sofr"] is None
    assert known["compositeLiquidityScore"] is None
