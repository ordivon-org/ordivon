from __future__ import annotations

from domains.decision_intake.models import DecisionIntake
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

    def validate_intake(
        self,
        intake: DecisionIntake,
        advisory_hints: list[GovernanceAdvisoryHint] | tuple[GovernanceAdvisoryHint, ...] | None = None,
    ) -> GovernanceDecision:
        reasons = []
        hints = tuple(advisory_hints or ())
        snapshot = self.policy_source.get_active_snapshot()
        
        # We specifically want the TradingDisciplinePolicy for intake.
        # Currently policy_source.get_active_policies() returns all policies.
        # Some policies (like ForbiddenSymbolsPolicy) might not take 'intake' as argument.
        # Let's iterate and safely call them if they support it, or hardcode it for now.
        from packs.finance.trading_discipline import TradingDisciplinePolicy
        policy = TradingDisciplinePolicy()
        violations = policy.check(intake)
        reasons.extend(violations)
            
        if reasons:
            decision = "reject"
            # Borderline condition check for escalation
            if any("Chasing" in v for v in reasons) and not any("Revenge" in v for v in reasons):
                confidence = intake.payload.get("confidence")
                if confidence is not None and confidence >= 0.8:
                    decision = "escalate"
                    
            return GovernanceDecision(
                decision=decision,
                reasons=reasons,
                source="risk_engine.trading_discipline_policy",
                advisory_hints=hints,
                policy_set_id=snapshot.policy_set_id,
                active_policy_ids=snapshot.active_policy_ids,
                default_decision_rule_ids=snapshot.default_decision_rule_ids,
            )

        return GovernanceDecision(
            decision="execute",
            reasons=["Passed trading discipline validation."],
            source="risk_engine.trading_discipline_policy",
            advisory_hints=hints,
            policy_set_id=snapshot.policy_set_id,
            active_policy_ids=snapshot.active_policy_ids,
            default_decision_rule_ids=snapshot.default_decision_rule_ids,
        )
