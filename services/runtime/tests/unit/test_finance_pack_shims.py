from orchestrator.context.context_builder import ContextBuilder
from orchestrator.context.market_context import MarketContext
from orchestrator.context.portfolio_context import PortfolioContext
from domains.research.models import AnalysisRequest
from packs.finance.context import build_finance_analysis_context_defaults


def test_finance_pack_defaults_own_market_and_portfolio_context():
    defaults = build_finance_analysis_context_defaults(symbol="BTC/USDT", timeframe="1h")

    assert defaults.market.symbol == "BTC/USDT"
    assert defaults.market.timeframe == "1h"
    assert defaults.portfolio.cash_balance == 0.0


def test_orchestration_context_modules_remain_shims():
    market = MarketContext(symbol="BTC/USDT", timeframe="4h")
    portfolio = PortfolioContext()

    assert market.symbol == "BTC/USDT"
    assert portfolio.positions == []


def test_context_builder_uses_finance_pack_defaults_without_changing_callers():
    ctx = ContextBuilder().build(AnalysisRequest(query="Analyze BTC", symbol="BTC/USDT", timeframe="1d"))

    assert ctx.market.symbol == "BTC/USDT"
    assert ctx.market.timeframe == "1d"
    assert ctx.portfolio.cash_balance == 0.0
