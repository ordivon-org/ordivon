from domains.research.models import AnalysisResult
from governance.decision import GovernanceAdvisoryHint, GovernanceDecision
from governance.policy_source import GovernancePolicySource


class RiskEngine:
    def __init__(self):
        self.policy_source = GovernancePolicySource()

    def validate_analysis(
        self,
        analysis: AnalysisResult,
        advisory_hints: list[GovernanceAdvisoryHint] | tuple[GovernanceAdvisoryHint, ...] | None = None,
    ) -> GovernanceDecision:
        reasons = []
        hints = tuple(advisory_hints or ())
        snapshot = self.policy_source.get_active_snapshot()
        for policy in self.policy_source.get_active_policies():
            violations = policy.check(analysis)
            reasons.extend(violations)
            
        if reasons:
            return GovernanceDecision(
                decision="reject",
                reasons=reasons,
                source="risk_engine.forbidden_symbols_policy",
                advisory_hints=hints,
                policy_set_id=snapshot.policy_set_id,
                active_policy_ids=snapshot.active_policy_ids,
                default_decision_rule_ids=snapshot.default_decision_rule_ids,
            )

        if not analysis.suggested_actions:
            return GovernanceDecision(
                decision="escalate",
                reasons=["No suggested actions were produced."],
                source="risk_engine.default_validation",
                advisory_hints=hints,
                policy_set_id=snapshot.policy_set_id,
                active_policy_ids=snapshot.active_policy_ids,
                default_decision_rule_ids=snapshot.default_decision_rule_ids,
            )

        return GovernanceDecision(
            decision="execute",
            reasons=["Passed default Step 1 governance validation."],
            source="risk_engine.default_validation",
            advisory_hints=hints,
            policy_set_id=snapshot.policy_set_id,
            active_policy_ids=snapshot.active_policy_ids,
            default_decision_rule_ids=snapshot.default_decision_rule_ids,
        )
