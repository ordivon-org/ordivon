from __future__ import annotations

from domains.decision_intake.models import DecisionIntake
from domains.research.models import AnalysisResult
from governance.decision import GovernanceAdvisoryHint, GovernanceDecision
from governance.policy_source import GovernancePolicySource
from packs.finance.trading_discipline_policy import RejectReason, EscalateReason

# ── H-5 Finance Decision Governance Hard Gate ──────────────────────────────
# Decision priority: reject > escalate > execute
#   - Any reject reason  → reject
#   - Else any escalate reason → escalate
#   - Else → execute
#
# Hard gate rules (ordered by severity):
#   REJECT: invalid intake, missing thesis/stop_loss/emotional_state/
#           max_loss_usdt/position_size_usdt/risk_unit_usdt,
#           max_loss > 2× risk_unit, position_size > 10× risk_unit
#   ESCALATE: is_revenge_trade=true, is_chasing=true
#   EXECUTE: all fields valid, no behavioural red flags
# ───────────────────────────────────────────────────────────────────────────

# Risk limits (from trading_limits.yaml policy):
_MAX_LOSS_TO_RISK_UNIT_RATIO = 2.0   # max_loss must be <= 2× risk_unit
_MAX_POSITION_TO_RISK_UNIT_RATIO = 10.0  # position_size must be <= 10× risk_unit


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
        pack_policy=None,  # ADR-006: optional Pack policy for domain validation
        advisory_hints: list[GovernanceAdvisoryHint] | tuple[GovernanceAdvisoryHint, ...] | None = None,
    ) -> GovernanceDecision:
        """Evaluate a DecisionIntake and return execute/escalate/reject.

        Gate 0 (generic — stays in Core): intake must be validated.
        Gates 1-4 (delegated to pack_policy per ADR-006): domain-specific.
        If no pack_policy provided, all gates pass → execute.
        Decision priority: reject > escalate > execute.
        """
        hints = tuple(advisory_hints or ())
        snapshot = self.policy_source.get_active_snapshot()

        reject_reasons: list[str] = []
        escalate_reasons: list[str] = []

        # ── Gate 0: Intake must be validated (generic) ──────────────
        if intake.status != "validated":
            reject_reasons.append(
                f"Intake status is '{intake.status}' — "
                f"only validated intakes can be governed."
            )

        # ── Gates 1-4: Delegated to pack policy (ADR-006) ──────────
        if pack_policy is not None and intake.payload:
            payload = intake.payload

            for reason in pack_policy.validate_fields(payload):
                if isinstance(reason, RejectReason):
                    reject_reasons.append(reason.message)
                elif isinstance(reason, EscalateReason):
                    escalate_reasons.append(reason.message)

            for reason in pack_policy.validate_numeric(payload):
                reject_reasons.append(reason.message)

            for reason in pack_policy.validate_limits(payload):
                reject_reasons.append(reason.message)

            for reason in pack_policy.validate_behavioral(payload):
                escalate_reasons.append(reason.message)

        # ── Decision (priority: reject > escalate > execute) ───────
        if reject_reasons:
            return GovernanceDecision(
                decision="reject",
                reasons=reject_reasons,
                source="risk_engine.finance_governance_hard_gate",
                advisory_hints=hints,
                policy_set_id=snapshot.policy_set_id,
                active_policy_ids=snapshot.active_policy_ids,
                default_decision_rule_ids=snapshot.default_decision_rule_ids,
            )

        if escalate_reasons:
            return GovernanceDecision(
                decision="escalate",
                reasons=escalate_reasons,
                source="risk_engine.finance_governance_hard_gate",
                advisory_hints=hints,
                policy_set_id=snapshot.policy_set_id,
                active_policy_ids=snapshot.active_policy_ids,
                default_decision_rule_ids=snapshot.default_decision_rule_ids,
            )

        return GovernanceDecision(
            decision="execute",
            reasons=["Passed all governance gates."],
            source="risk_engine.finance_governance_hard_gate",
            advisory_hints=hints,
            policy_set_id=snapshot.policy_set_id,
            active_policy_ids=snapshot.active_policy_ids,
            default_decision_rule_ids=snapshot.default_decision_rule_ids,
        )


# ── Private helpers ────────────────────────────────────────────────────────

def _as_str(value: object) -> str | None:
    """Normalize a payload value to a non-empty string, or None."""
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _as_positive_float(value: object) -> float | None:
    """Normalize a payload value to a positive float, or None."""
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


# ── Emotional risk keyword detection ────────────────────────────────────────

_EMOTIONAL_RISK_KEYWORDS: frozenset[str] = frozenset({
    "stress", "stressed", "stressful",
    "fear", "fearful", "scared", "terrified", "panicked", "panic",
    "anger", "angry", "furious", "frustrated",
    "fomo", "greedy", "desperate", "reckless",
    "revenge", "impulsive",
})


def _contains_emotional_risk(emotional_state: str) -> bool:
    """Return True if emotional_state contains known risk keywords.

    Case-insensitive substring match against the tokenized input.
    """
    lowered = emotional_state.lower()
    return any(keyword in lowered for keyword in _EMOTIONAL_RISK_KEYWORDS)
