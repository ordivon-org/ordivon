from dataclasses import dataclass, field

from pfios.domain.analysis.models import AnalysisResult


@dataclass
class GovernanceDecision:
    allowed: bool
    reasons: list[str] = field(default_factory=list)


class RiskEngine:
    def validate_analysis(self, analysis: AnalysisResult) -> GovernanceDecision:
        if not analysis.suggested_actions:
            return GovernanceDecision(
                allowed=False,
                reasons=["No suggested actions were produced."],
            )

        return GovernanceDecision(
            allowed=True,
            reasons=["Passed default Step 1 governance validation."],
        )
