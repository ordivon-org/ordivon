from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


_SURFACE_OPTIONS = json.loads((Path(__file__).with_name("analyze_surface_options.json")).read_text(encoding="utf-8"))

DEFAULT_FINANCE_SYMBOL = str(_SURFACE_OPTIONS["defaultSymbol"])
DEFAULT_FINANCE_TIMEFRAME = str(_SURFACE_OPTIONS["defaultTimeframe"])
SUPPORTED_FINANCE_SYMBOLS = tuple(str(item) for item in _SURFACE_OPTIONS["supportedSymbols"])
SUPPORTED_FINANCE_TIMEFRAMES = tuple(str(item) for item in _SURFACE_OPTIONS["supportedTimeframes"])


@dataclass(frozen=True, slots=True)
class FinanceAnalyzeProfile:
    symbol: str
    timeframe: str
    supported_symbols: tuple[str, ...] = SUPPORTED_FINANCE_SYMBOLS
    supported_timeframes: tuple[str, ...] = SUPPORTED_FINANCE_TIMEFRAMES


def build_finance_analyze_profile(
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
) -> FinanceAnalyzeProfile:
    resolved_symbol = symbol or DEFAULT_FINANCE_SYMBOL
    resolved_timeframe = timeframe if timeframe in SUPPORTED_FINANCE_TIMEFRAMES else DEFAULT_FINANCE_TIMEFRAME
    return FinanceAnalyzeProfile(symbol=resolved_symbol, timeframe=resolved_timeframe)
