from __future__ import annotations

from domains.decision_intake.models import DecisionIntake
from domains.research.models import AnalysisResult
from governance.decision import GovernanceAdvisoryHint, GovernanceDecision
from governance.policy_source import GovernancePolicySource
from governance.risk_engine.thesis_quality import check_thesis_quality

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
        advisory_hints: list[GovernanceAdvisoryHint] | tuple[GovernanceAdvisoryHint, ...] | None = None,
    ) -> GovernanceDecision:
        """H-5 Finance Decision Governance Hard Gate.

        Evaluates a DecisionIntake and returns a deterministic
        execute / escalate / reject decision with priority:
        reject > escalate > execute.
        """
        hints = tuple(advisory_hints or ())
        snapshot = self.policy_source.get_active_snapshot()

        reject_reasons: list[str] = []
        escalate_reasons: list[str] = []

        # ── Gate 0: Intake must be validated ──────────────────────────
        if intake.status != "validated":
            reject_reasons.append(
                f"Intake status is '{intake.status}' — only validated intakes can be governed."
            )

        payload = intake.payload

        # ── Gate 1: Required discipline fields (missing → reject) ────
        thesis = _as_str(payload.get("thesis"))
        if not thesis:
            reject_reasons.append("Missing required field: thesis.")

        # H-9C3: Thesis quality checks (only if thesis is present)
        if thesis:
            quality = check_thesis_quality(thesis)
            if quality.is_banned:
                reject_reasons.append(
                    f"Thesis quality rejected: {quality.banned_match or 'generic pattern'}."
                )
            if quality.is_too_short:
                escalate_reasons.append(
                    f"Thesis is too short ({len(thesis.strip())} chars, "
                    f"minimum 50) — requires human review."
                )
            if quality.lacks_verifiability:
                escalate_reasons.append(
                    "Thesis lacks verifiability criteria (no invalidation "
                    "or confirmation conditions) — requires human review."
                )

        stop_loss = _as_str(payload.get("stop_loss"))
        if not stop_loss:
            reject_reasons.append("Missing required field: stop_loss.")

        emotional_state = _as_str(payload.get("emotional_state"))
        if not emotional_state:
            reject_reasons.append("Missing required field: emotional_state.")

        # ── Gate 2: Required numeric fields (missing/zero → reject) ──
        max_loss = _as_positive_float(payload.get("max_loss_usdt"))
        if max_loss is None:
            reject_reasons.append("Missing or non-positive field: max_loss_usdt.")

        position_size = _as_positive_float(payload.get("position_size_usdt"))
        if position_size is None:
            reject_reasons.append("Missing or non-positive field: position_size_usdt.")

        risk_unit = _as_positive_float(payload.get("risk_unit_usdt"))
        if risk_unit is None:
            reject_reasons.append("Missing or non-positive field: risk_unit_usdt.")

        # ── Gate 3: Risk limit violations (only if numeric fields present) ──
        if max_loss is not None and risk_unit is not None and risk_unit > 0:
            if max_loss > _MAX_LOSS_TO_RISK_UNIT_RATIO * risk_unit:
                reject_reasons.append(
                    f"max_loss_usdt ({max_loss}) exceeds {_MAX_LOSS_TO_RISK_UNIT_RATIO}× "
                    f"risk_unit_usdt ({risk_unit}), max allowed: {_MAX_LOSS_TO_RISK_UNIT_RATIO * risk_unit}."
                )

        if position_size is not None and risk_unit is not None and risk_unit > 0:
            if position_size > _MAX_POSITION_TO_RISK_UNIT_RATIO * risk_unit:
                reject_reasons.append(
                    f"position_size_usdt ({position_size}) exceeds "
                    f"{_MAX_POSITION_TO_RISK_UNIT_RATIO}× "
                    f"risk_unit_usdt ({risk_unit}), max allowed: {_MAX_POSITION_TO_RISK_UNIT_RATIO * risk_unit}."
                )

        # ── Gate 4: Behavioural red flags (escalate, not reject) ─────
        if payload.get("is_revenge_trade") is True:
            escalate_reasons.append("is_revenge_trade=true — requires human review.")

        if payload.get("is_chasing") is True:
            escalate_reasons.append("is_chasing=true — requires human review.")

        # H-9C2: Emotional state risk indicators → escalate
        emotional = _as_str(payload.get("emotional_state"))
        if emotional and _contains_emotional_risk(emotional):
            escalate_reasons.append(
                f"emotional_state='{emotional}' indicates elevated risk — "
                f"requires human review."
            )

        # H-9C2: Rule exceptions present → escalate (any exception needs review)
        rule_exceptions = payload.get("rule_exceptions")
        if isinstance(rule_exceptions, list) and len(rule_exceptions) > 0:
            escalate_reasons.append(
                f"rule_exceptions not empty ({len(rule_exceptions)} item(s)) — "
                f"requires human review."
            )

        # H-9C2: Confidence too low → escalate (but not missing, which is not checked here)
        confidence = payload.get("confidence")
        if isinstance(confidence, (int, float)) and 0 <= confidence < 0.3:
            escalate_reasons.append(
                f"confidence={confidence} is below 0.3 threshold — "
                f"requires human review."
            )

        # ── Decision (priority: reject > escalate > execute) ─────────
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
            reasons=["Passed H-5 Finance Governance Hard Gate."],
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
