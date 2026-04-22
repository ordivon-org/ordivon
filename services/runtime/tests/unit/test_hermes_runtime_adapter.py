from adapters.runtimes.hermes.runtime import HermesRuntime
from intelligence.runtime.hermes_client import HermesClient
from orchestrator.context.context_builder import AnalysisContext
from orchestrator.context.governance_context import GovernanceContext
from orchestrator.context.market_context import MarketContext
from orchestrator.context.memory_context import MemoryContext
from orchestrator.context.portfolio_context import PortfolioContext
from orchestrator.context.query_context import QueryContext


class _FakeHermesClient(HermesClient):
    def __init__(self) -> None:
        pass

    def health_check(self) -> dict:
        return {"status": "ok", "provider": "gemini", "model": "stub-model"}

    def run_task(self, task_type: str, payload: dict) -> dict:
        return {
            "task_id": payload["task_id"],
            "task_type": task_type,
            "idempotency_key": payload["idempotency_key"],
            "trace_id": payload["trace_id"],
            "input": payload["input"],
            "status": "completed",
            "provider": "gemini",
            "model": "stub-model",
            "session_id": "sess_test",
            "started_at": "2026-04-22T00:00:00+00:00",
            "completed_at": "2026-04-22T00:00:01+00:00",
            "output": {
                "summary": "Adapter summary",
                "thesis": "Adapter thesis",
                "risks": ["risk_a"],
                "suggested_actions": ["action_a"],
            },
            "tool_trace": [],
            "memory_events": [],
            "delegation_trace": [],
            "usage": {"total_tokens": 12},
            "error": None,
        }


def _ctx() -> AnalysisContext:
    return AnalysisContext(
        query=QueryContext(query="Analyze BTC"),
        market=MarketContext(symbol="BTC/USDT", timeframe="1h"),
        portfolio=PortfolioContext(),
        memory=MemoryContext(),
        governance=GovernanceContext(active_policies=["forbidden_symbols_policy"]),
    )


def test_hermes_runtime_exposes_health_and_runtime_capabilities():
    runtime = HermesRuntime(client=_FakeHermesClient())

    assert runtime.health()["status"] == "ok"
    assert runtime.supports_memory_policy() is True
    assert runtime.supports_progress() is False
    assert runtime.descriptor.provider_name == "hermes"


def test_hermes_runtime_analyze_returns_analysis_result():
    runtime = HermesRuntime(client=_FakeHermesClient())

    analysis = runtime.analyze(_ctx())

    assert analysis.summary == "Adapter summary"
    assert analysis.thesis == "Adapter thesis"
    assert analysis.metadata["runtime_adapter"] == "adapters.runtimes.hermes.runtime.HermesRuntime"
