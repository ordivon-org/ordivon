"""Native Markets source boundary: Cboe raw bars must not poison Qlib HILO."""
from importlib import import_module

import pandas as pd
import pytest


def _raw_qqq_iwm() -> dict[str, pd.DataFrame]:
    # Actual prices observed in preserved raw Cboe captures, not synthetic
    # corrected bars or adjusted economic total returns.
    return {
        "QQQ": pd.DataFrame({
            "open": [705.29], "high": [713.13], "low": [703.79],
            "close": [713.15], "volume": [31669837],
        }, index=["2026-05-20"]),
        "IWM": pd.DataFrame({
            "open": [181.37], "high": [180.82], "low": [178.44],
            "close": [179.58], "volume": [32257721],
        }, index=["2023-06-05"]),
    }


@pytest.mark.parametrize("symbol", ("QQQ", "IWM"))
def test_raw_provider_hilo_source_must_reject_impossible_observed_bar(symbol):
    """The Qlib HILO feature must never consume an impossible OHLC candle."""
    owner = import_module("ordivon_capital.markets.equity_ohlcv_shape")
    with pytest.raises(owner.EquityOhlcvShapeError, match="OHLC_BOUNDS_INVALID_FOR_HILO"):
        owner.require_ohlcv_shape_for_hilo(_raw_qqq_iwm()[symbol], symbol=symbol)


def test_source_shape_does_not_claim_adjustment_pit_or_data_rights():
    owner = import_module("ordivon_capital.markets.equity_ohlcv_shape")
    clean = _raw_qqq_iwm()["QQQ"].copy()
    clean.loc["2026-05-20", "high"] = 713.15
    original = clean.copy(deep=True)
    result = owner.require_ohlcv_shape_for_hilo(clean, symbol="QQQ")
    pd.testing.assert_frame_equal(clean, original)
    assert result["standing"] == "STRUCTURALLY_COHERENT_OHLCV_SOURCE_UNATTESTED"
    assert result["priceIssuerAdjustmentVerified"] is False
    assert result["issuerHistoricalPITVerified"] is False
    assert result["externalDataRightsVerified"] is False
    assert result["capitalAuthority"] is False


@pytest.mark.parametrize("field", ("open", "high", "low", "close", "volume"))
def test_vendor_boolean_is_not_a_market_numeric_observation(field):
    owner = import_module("ordivon_capital.markets.equity_ohlcv_shape")
    clean = _raw_qqq_iwm()["QQQ"].copy().astype(object)
    clean.loc["2026-05-20", "high"] = 713.15
    clean.loc["2026-05-20", field] = True
    with pytest.raises(owner.EquityOhlcvShapeError, match="boolean OHLCV"):
        owner.require_ohlcv_shape_for_hilo(clean, symbol="QQQ")


def test_invalid_vendor_volume_nan_duplicates_and_missing_columns_fail():
    owner = import_module("ordivon_capital.markets.equity_ohlcv_shape")
    base = _raw_qqq_iwm()["QQQ"].copy()
    base.loc["2026-05-20", "high"] = 713.15
    invalid_volume = base.copy()
    invalid_volume.loc["2026-05-20", "volume"] = -1
    with pytest.raises(owner.EquityOhlcvShapeError, match="OHLC_BOUNDS_INVALID"):
        owner.require_ohlcv_shape_for_hilo(invalid_volume, symbol="QQQ")
    invalid_nan = base.copy()
    invalid_nan.loc["2026-05-20", "low"] = float("nan")
    with pytest.raises(owner.EquityOhlcvShapeError, match="nonfinite"):
        owner.require_ohlcv_shape_for_hilo(invalid_nan, symbol="QQQ")
    duplicated = base.copy()
    duplicated["high2"] = duplicated["high"]
    duplicated.columns = ["open", "high", "low", "close", "volume", "high"]
    with pytest.raises(owner.EquityOhlcvShapeError, match="exactly one"):
        owner.require_ohlcv_shape_for_hilo(duplicated, symbol="QQQ")
    with pytest.raises(owner.EquityOhlcvShapeError, match="exactly one"):
        owner.require_ohlcv_shape_for_hilo(base.drop(columns=["high"]), symbol="QQQ")
