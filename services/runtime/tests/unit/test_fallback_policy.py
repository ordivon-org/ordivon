from orchestrator.runtime.recovery import FallbackDecision, FallbackResult


def test_fallback_contract_is_degraded_not_success():
    decision = FallbackDecision(
        action="degraded_analysis", reason="runtime down", detail={"fallback_type": "degraded_analysis"}
    )
    result = FallbackResult(status="degraded", detail={"reason": "runtime down"})

    assert decision.action == "degraded_analysis"
    assert result.status == "degraded"
