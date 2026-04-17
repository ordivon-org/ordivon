from dataclasses import dataclass

from pfios.context.query_context import QueryContext
from pfios.context.market_context import MarketContext
from pfios.context.portfolio_context import PortfolioContext
from pfios.context.memory_context import MemoryContext
from pfios.context.governance_context import GovernanceContext
from pfios.domain.analysis.models import AnalysisRequest


@dataclass
class AnalysisContext:
    query: QueryContext
    market: MarketContext
    portfolio: PortfolioContext
    memory: MemoryContext
    governance: GovernanceContext


class ContextBuilder:
    def build(self, request: AnalysisRequest) -> AnalysisContext:
        return AnalysisContext(
            query=QueryContext(query=request.query),
            market=MarketContext(symbol=request.symbol, timeframe=request.timeframe),
            portfolio=PortfolioContext(),
            memory=MemoryContext(),
            governance=GovernanceContext(active_policies=["default_risk_policy"]),
        )
