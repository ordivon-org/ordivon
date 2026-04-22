from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MarketContext:
    symbol: str | None = None
    timeframe: str | None = None
    signals: dict = field(default_factory=dict)


@dataclass
class PortfolioContext:
    positions: list[dict] = field(default_factory=list)
    cash_balance: float = 0.0


@dataclass(frozen=True, slots=True)
class FinanceAnalysisContextDefaults:
    market: MarketContext
    portfolio: PortfolioContext


def build_finance_analysis_context_defaults(
    *,
    symbol: str | None = None,
    timeframe: str | None = None,
) -> FinanceAnalysisContextDefaults:
    return FinanceAnalysisContextDefaults(
        market=MarketContext(symbol=symbol, timeframe=timeframe),
        portfolio=PortfolioContext(),
    )
