import pytest

from capabilities.workflow.analyze import AnalyzeCapability, AnalyzeCapabilityInput
from packs.finance.analyze_defaults import build_finance_analyze_defaults


class _StubOrchestrator:
    def __init__(self) -> None:
        self.requests = []

    def execute_analyze(self, request, db=None):
        self.requests.append(request)
        return {
            "summary": "stub",
            "risks": [],
            "suggested_actions": [],
            "analysis_id": "analysis_stub",
            "recommendation_id": "reco_stub",
            "governance": {"decision": "reject", "source": "test", "reasons": []},
        }


def test_finance_analyze_defaults_provide_pack_owned_symbol_and_timeframe():
    defaults = build_finance_analyze_defaults()

    assert defaults.symbol == "BTC/USDT"
    assert defaults.timeframe == "1h"


@pytest.mark.anyio
async def test_analyze_capability_uses_finance_pack_defaults_when_symbol_missing():
    orchestrator = _StubOrchestrator()
    capability = AnalyzeCapability(orchestrator=orchestrator)

    await capability.analyze_and_suggest(AnalyzeCapabilityInput(query="test", symbols=[]))

    request = orchestrator.requests[0]
    assert request.symbol == "BTC/USDT"
    assert request.timeframe == "1h"
