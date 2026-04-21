from __future__ import annotations

from orchestrator.context.context_builder import AnalysisContext
from shared.config.settings import settings
from shared.utils.ids import new_id
from intelligence.tasks.contracts import (
    AnalysisTaskInput,
    AnalysisTaskResultBundle,
    IntelligenceTaskRequest,
    TaskConstraints,
    TaskContextRefs,
    TaskExecutionPolicy,
    TaskLineage,
)


def build_analysis_task(ctx: AnalysisContext) -> IntelligenceTaskRequest:
    trace_id = new_id("trace")
    task_id = new_id("task")
    symbol = ctx.market.symbol or "UNKNOWN"
    return IntelligenceTaskRequest(
        task_id=task_id,
        idempotency_key=task_id,
        trace_id=trace_id,
        input=AnalysisTaskInput(
            query=ctx.query.query,
            symbol=symbol,
            timeframe=ctx.market.timeframe,
            market_signals=ctx.market.signals,
            memory_lessons=ctx.memory.lessons,
            related_reviews=ctx.memory.related_reviews,
            active_policies=ctx.governance.active_policies,
            risk_mode=ctx.governance.risk_mode,
            portfolio_cash_balance=ctx.portfolio.cash_balance,
            portfolio_positions=ctx.portfolio.positions,
        ),
        context_refs=TaskContextRefs(
            provider=settings.hermes_default_provider,
            model=settings.hermes_default_model,
        ),
        lineage=TaskLineage(
            query=ctx.query.query,
            symbol=symbol,
            timeframe=ctx.market.timeframe,
        ),
        constraints=TaskConstraints(
            must_return_fields=["summary", "thesis", "risks", "suggested_actions"],
        ),
        execution_policy=TaskExecutionPolicy(
            enable_delegation=settings.hermes_enable_delegation,
            enable_memory=settings.hermes_enable_memory,
            enable_moa=settings.hermes_enable_moa,
        ),
        reason=f"Generate analysis for {symbol} in PFIOS analyze workflow.",
        actor="pfios.analyze",
        context="analyze.workflow",
    )


def normalize_analysis_output(
    request: IntelligenceTaskRequest,
    response: dict[str, object],
) -> AnalysisTaskResultBundle:
    return AnalysisTaskResultBundle.from_runtime_response(request, response)
