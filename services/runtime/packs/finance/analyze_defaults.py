from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FinanceAnalyzeDefaults:
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"


def build_finance_analyze_defaults(*, symbol: str | None = None, timeframe: str | None = None) -> FinanceAnalyzeDefaults:
    return FinanceAnalyzeDefaults(
        symbol=symbol or "BTC/USDT",
        timeframe=timeframe or "1h",
    )
