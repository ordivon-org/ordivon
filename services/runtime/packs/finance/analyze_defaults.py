from __future__ import annotations

from dataclasses import dataclass

from packs.finance.analyze_profile import DEFAULT_FINANCE_SYMBOL, DEFAULT_FINANCE_TIMEFRAME


@dataclass(frozen=True, slots=True)
class FinanceAnalyzeDefaults:
    symbol: str = DEFAULT_FINANCE_SYMBOL
    timeframe: str = DEFAULT_FINANCE_TIMEFRAME


def build_finance_analyze_defaults(
    *, symbol: str | None = None, timeframe: str | None = None
) -> FinanceAnalyzeDefaults:
    return FinanceAnalyzeDefaults(
        symbol=symbol or DEFAULT_FINANCE_SYMBOL,
        timeframe=timeframe or DEFAULT_FINANCE_TIMEFRAME,
    )
