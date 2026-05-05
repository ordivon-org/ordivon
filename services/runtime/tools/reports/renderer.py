from governance_engine.decision import GovernanceDecision
from domains.research.models import AnalysisResult


class ReportRenderer:
    def render_analysis_report(
        self,
        analysis: AnalysisResult,
        governance: GovernanceDecision,
    ) -> dict:
        return {
            "analysis_id": analysis.id,
            "summary": analysis.summary,
            "thesis": analysis.thesis,
            "risks": analysis.risks,
            "suggested_actions": analysis.suggested_actions,
            "governance": {
                "decision": governance.decision,
                "allowed": governance.allowed,
                "reasons": governance.reasons,
                "source": governance.source,
                "policy_set_id": governance.policy_set_id,
                "active_policy_ids": list(governance.active_policy_ids),
                "default_decision_rule_ids": list(governance.default_decision_rule_ids),
                "advisory_hints": [hint.to_payload() for hint in governance.advisory_hints],
            },
            "metadata": analysis.metadata,
            "created_at": analysis.created_at,
        }
