from governance_engine.risk_engine.engine import GovernanceDecision
from domains.research.models import AnalysisResult
from tools.reports.renderer import ReportRenderer


def test_report_renderer_returns_execution_payload():
    renderer = ReportRenderer()
    payload = renderer.render_analysis_report(
        AnalysisResult(
            summary="summary",
            thesis="thesis",
            risks=["risk"],
            suggested_actions=["act"],
            metadata={"provider": "mock"},
        ),
        GovernanceDecision(decision="execute", reasons=["ok"], source="test-suite"),
    )

    assert payload["summary"] == "summary"
    assert payload["governance"]["decision"] == "execute"
    assert payload["governance"]["allowed"] is True
    assert payload["governance"]["source"] == "test-suite"
    assert payload["governance"]["policy_set_id"] == "governance.unknown"
    assert payload["suggested_actions"] == ["act"]
