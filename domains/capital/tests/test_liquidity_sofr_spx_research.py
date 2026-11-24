"""Falsify source, calendar and release-lag boundaries of the Research consumer."""

from __future__ import annotations

import csv
import importlib.util
import io
from datetime import date, timedelta
from pathlib import Path

import exchange_calendars as xcals
import pytest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/research/liquidity_sofr_spx_ablation.py"
spec = importlib.util.spec_from_file_location("liquidity_sofr_spx_ablation", SOURCE)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def _csv(headers: list[str], values: list[tuple]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(values)
    return output.getvalue().encode()


def _price_fixture() -> bytes:
    days = xcals.get_calendar("XNYS").sessions_in_range(m.PRICE_START, m.PRICE_END)
    return _csv(
        ["DATE", "SPX"], [(day.strftime("%m/%d/%Y"), 1000 + i) for i, day in enumerate(days)]
    )


def _funding_fixture() -> bytes:
    return _csv(
        [
            "Effective Date",
            "Rate Type",
            "Rate (%)",
            "1st Percentile (%)",
            "99th Percentile (%)",
            "Volume ($Billions)",
            "Revision Indicator (Y/N)",
        ],
        [
            ("04/02/2018", "SOFR", "-0.01", "-0.03", "0.10", "100", ""),
            ("04/03/2018", "SOFR", "0.04", "0.01", "0.10", "110", ""),
            ("04/04/2018", "SOFR", "0.04", "NA", "NA", "120", ""),
            ("04/05/2018", "SOFR", "0.05", "0.01", "0.15", "120", ""),
        ],
    )


def test_negative_funding_percentiles_are_real_but_na_is_not_zero():
    days, prices, rates, missing = m.load_sources(spx=_price_fixture(), sofr=_funding_fixture())
    assert len(days) > 2000
    assert rates[date(2018, 4, 2)][0] == -0.01
    assert date(2018, 4, 4) not in rates
    assert missing == ["2018-04-04"]


def test_invented_exchange_holiday_rejected():
    text = _price_fixture().decode()
    assert "05/27/2025," in text
    injected = text.replace("05/27/2025,", "05/26/2025,10000\n05/27/2025,")
    with pytest.raises(ValueError, match="XNYS_SESSION_GRID_MISMATCH"):
        m.load_sources(spx=injected.encode(), sofr=_funding_fixture())


def test_revised_and_invalid_numeric_rows_rejected():
    text = _funding_fixture().decode()
    revised = text.replace(
        "04/03/2018,SOFR,0.04,0.01,0.10,110,", "04/03/2018,SOFR,0.04,0.01,0.10,110,Y"
    )
    with pytest.raises(ValueError, match="revision"):
        m.load_sources(spx=_price_fixture(), sofr=revised.encode())
    corrupt = text.replace("04/04/2018,SOFR,0.04,NA,NA,120,", "04/04/2018,SOFR,0.04,BAD,NA,120,")
    with pytest.raises(ValueError, match="unexpected funding field token"):
        m.load_sources(spx=_price_fixture(), sofr=corrupt.encode())


def _synthetic_source():
    start = date(2019, 1, 1)
    days = [
        start + timedelta(days=i) for i in range(1650) if (start + timedelta(days=i)).weekday() < 5
    ]
    prices = {d: 100 + i * 0.07 for i, d in enumerate(days)}
    rates = {
        d: (0.03 + 0.001 * (i % 5), 900.0 + i, 0.11 + 0.0002 * (i % 5)) for i, d in enumerate(days)
    }
    return days, prices, rates


def test_future_funding_observation_cannot_change_earlier_features():
    days, prices, rates = _synthetic_source()
    rows = m.make_dataset(days, prices, rates)
    chosen = next(r for r in rows if r["index"] == 150)
    assert chosen["effective"] <= chosen["latest_usable_cutoff"] < chosen["decision"]
    modified = dict(rates)
    modified[days[151]] = (99.0, 999999.0, 99.0)  # future relative to decision
    after = m.make_dataset(days, prices, modified)
    assert next(r for r in after if r["index"] == 150) == chosen
    with pytest.raises(ValueError, match="same close"):
        m.make_dataset(days, prices, rates, lag=0)


def test_expanding_training_never_sees_open_outcome_window():
    days, prices, rates = _synthetic_source()
    rows = m.make_dataset(days, prices, rates)
    k = m.MIN_TRAINING + m.HORIZON + 1
    matured = m._matured_rows(rows, k)
    assert len(matured) >= m.MIN_TRAINING
    assert all(r["index"] + m.HORIZON + 1 <= rows[k]["index"] for r in matured)
    assert all(r["index"] + m.HORIZON + 1 > rows[k]["index"] for r in rows[k - 4 : k])


def test_model_is_an_unpromoted_readonly_research_consumer():
    code = SOURCE.read_text()
    assert "RETROSPECTIVE_LATEST_SNAPSHOT_ONLY_NOT_PIT_OR_ALPHA" in code
    assert "nontradeable index" in code
    assert "broker" in code.lower()
    assert "urllib" not in code and "psycopg" not in code
