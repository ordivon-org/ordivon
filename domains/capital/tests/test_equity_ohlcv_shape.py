"""Source-level falsification: no impossible OHLC bars reach Qlib HILO."""
from __future__ import annotations

import pandas as pd
import pytest

from ordivon_capital.markets.equity_ohlcv_shape import (
    EquityOhlcvShapeError,
    require_ohlcv_shape_for_hilo,
)


def valid():
    return pd.DataFrame({
        "open": [705.29, 181.37],
        "high": [713.15, 182.00],
        "low": [703.79, 178.44],
        "close": [713.15, 179.58],
        "volume": [36779200, 1000000],
    }, index=["2026-05-20", "2023-06-05"])


def test_coherent_source_qualifies_shape_but_not_pit_or_total_return():
    report = require_ohlcv_shape_for_hilo(valid(), symbol="QQQ")
    assert report["rows"] == 2
    assert report["standing"] == "STRUCTURALLY_COHERENT_OHLCV_SOURCE_UNATTESTED"
    assert report["priceIssuerAdjustmentVerified"] is False
    assert report["issuerHistoricalPITVerified"] is False
    assert report["capitalAuthority"] is False


@pytest.mark.parametrize(
    ("column", "row", "value", "message"),
    [
        ("high", 0, 713.13, "OHLC_BOUNDS_INVALID_FOR_HILO"),
        ("high", 1, 180.82, "OHLC_BOUNDS_INVALID_FOR_HILO"),
        ("low", 0, 705.30, "OHLC_BOUNDS_INVALID_FOR_HILO"),
        ("volume", 0, -1, "OHLC_BOUNDS_INVALID_FOR_HILO"),
        ("open", 0, 0, "OHLC_BOUNDS_INVALID_FOR_HILO"),
        ("close", 0, float("nan"), "nonfinite"),
        ("high", 0, "not-a-number", "nonnumeric"),
    ],
)
def test_raw_vendor_anomalies_cannot_be_silently_normalized(column, row, value, message):
    frame = valid()
    if isinstance(value, str):
        frame[column] = frame[column].astype(object)
    frame.at[frame.index[row], column] = value
    with pytest.raises(EquityOhlcvShapeError, match=message):
        require_ohlcv_shape_for_hilo(frame, symbol="QQQ")


def test_missing_duplicate_primitive_does_not_admit_vendor_bar():
    frame = valid()
    frame["high2"] = frame["high"]
    frame.columns = ["open", "high", "low", "close", "volume", "high"]
    with pytest.raises(EquityOhlcvShapeError, match="exactly one"):
        require_ohlcv_shape_for_hilo(frame, symbol="IWM")


def test_only_bounded_usable_dataframes_admitted():
    for source in ({}, pd.DataFrame()):
        with pytest.raises(EquityOhlcvShapeError, match="nonempty"):
            require_ohlcv_shape_for_hilo(source, symbol="SPY")
