from dataclasses import dataclass

from orchestrator.context.governance_context import GovernanceContext
from orchestrator.context.market_context import MarketContext
from orchestrator.context.memory_context import MemoryContext
from orchestrator.context.portfolio_context import PortfolioContext
from orchestrator.context.query_context import QueryContext
from domains.research.models import AnalysisRequest


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
