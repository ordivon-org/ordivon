from pfios.domain.analysis.models import AnalysisResult
from pfios.governance.risk_engine.engine import GovernanceDecision


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
                "allowed": governance.allowed,
                "reasons": governance.reasons,
            },
            "metadata": analysis.metadata,
            "created_at": analysis.created_at,
        }
