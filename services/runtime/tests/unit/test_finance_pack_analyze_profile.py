from packs.finance.analyze_profile import (
    DEFAULT_FINANCE_SYMBOL,
    DEFAULT_FINANCE_TIMEFRAME,
    SUPPORTED_FINANCE_SYMBOLS,
    SUPPORTED_FINANCE_TIMEFRAMES,
    build_finance_analyze_profile,
)


def test_finance_analyze_profile_uses_supported_inputs():
    profile = build_finance_analyze_profile(symbol="ETH/USDT", timeframe="4h")

    assert profile.symbol == "ETH/USDT"
    assert profile.timeframe == "4h"
    assert profile.supported_symbols == SUPPORTED_FINANCE_SYMBOLS
    assert profile.supported_timeframes == SUPPORTED_FINANCE_TIMEFRAMES


def test_finance_analyze_profile_falls_back_for_unsupported_inputs():
    profile = build_finance_analyze_profile(symbol="DOGE/USDT", timeframe="30m")

    assert profile.symbol == "DOGE/USDT"
    assert profile.timeframe == DEFAULT_FINANCE_TIMEFRAME
