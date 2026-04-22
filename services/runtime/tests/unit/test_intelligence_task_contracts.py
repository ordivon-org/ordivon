import pytest

from intelligence.runtime.policy import MemoryPolicy
from intelligence.runtime.hermes_client import HermesTaskError
from intelligence.tasks.hermes import build_analysis_task, normalize_analysis_output
from orchestrator.context.context_builder import AnalysisContext


def _analysis_context() -> AnalysisContext:
    return AnalysisContext(
        query=type("QueryCtx", (), {"query": "Analyze BTC"})(),
        market=type(
            "MarketCtx",
            (),
            {
                "symbol": "BTC/USDT",
                "timeframe": "1d",
                "signals": {"trend": "up"},
            },
        )(),
        memory=type(
            "MemoryCtx",
            (),
            {
                "policy": MemoryPolicy(),
                "lessons": [{"id": "lesson_1"}],
                "related_reviews": [{"id": "review_1"}],
            },
        )(),
        governance=type(
            "GovernanceCtx",
            (),
            {
                "active_policies": [{"id": "policy_1"}],
                "risk_mode": "balanced",
            },
        )(),
        portfolio=type(
            "PortfolioCtx",
            (),
            {
                "cash_balance": 1000.0,
                "positions": [{"symbol": "BTC", "size": 1}],
            },
        )(),
    )


def test_build_analysis_task_returns_explicit_contract():
    request = build_analysis_task(_analysis_context())

    assert request.input.query == "Analyze BTC"
    assert request.input.symbol == "BTC/USDT"
    assert request.context_refs.provider
    assert request.execution_policy.enable_delegation is True
    assert request.to_payload()["input"]["query"] == "Analyze BTC"


def test_normalize_analysis_output_uses_request_contract_fields():
    request = build_analysis_task(_analysis_context())
    result = normalize_analysis_output(
        request,
        {
            "task_id": request.task_id,
            "task_type": "analysis.generate",
            "status": "completed",
            "provider": "gemini",
            "model": "google/gemini-3.1-pro-preview",
            "session_id": "sess_123",
            "trace_id": request.trace_id,
            "output": {
                "summary": "BTC remains constructive.",
                "thesis": "Momentum still supports continuation.",
                "risks": ["Volatility spike"],
                "suggested_actions": ["Monitor support"],
            },
            "tool_trace": [],
            "memory_events": [],
            "delegation_trace": [],
            "usage": {"total_tokens": 42},
            "started_at": "2026-04-19T00:00:00+00:00",
            "completed_at": "2026-04-19T00:00:01+00:00",
        },
    )

    assert result.summary == "BTC remains constructive."
    assert result.metadata.runtime_provider == "gemini"
    assert result.agent_action.input_summary == "Analyze BTC"
    assert result.agent_action.idempotency_key == request.idempotency_key


def test_normalize_analysis_output_rejects_malformed_payload():
    request = build_analysis_task(_analysis_context())

    with pytest.raises(HermesTaskError, match="output.summary"):
        normalize_analysis_output(
            request,
            {
                "task_id": request.task_id,
                "task_type": "analysis.generate",
                "status": "completed",
                "output": {
                    "summary": None,
                    "thesis": "ok",
                    "risks": [],
                    "suggested_actions": [],
                },
            },
        )
