# Finance-pack candidate: this module currently carries finance-shaped context defaults and should not become a core primitive owner.
from dataclasses import dataclass

from governance.policy_source import GovernancePolicySource
from orchestrator.context.governance_context import GovernanceContext
from orchestrator.context.market_context import MarketContext
from orchestrator.context.memory_context import MemoryContext
from orchestrator.context.portfolio_context import PortfolioContext
from orchestrator.context.query_context import QueryContext
from packs.finance.context import build_finance_analysis_context_defaults
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
        policy_snapshot = GovernancePolicySource().get_active_snapshot()
        finance_defaults = build_finance_analysis_context_defaults(
            symbol=request.symbol,
            timeframe=request.timeframe,
        )
        return AnalysisContext(
            query=QueryContext(query=request.query),
            market=finance_defaults.market,
            portfolio=finance_defaults.portfolio,
            memory=MemoryContext(),
            governance=GovernanceContext(active_policies=list(policy_snapshot.active_policy_ids)),
        )
