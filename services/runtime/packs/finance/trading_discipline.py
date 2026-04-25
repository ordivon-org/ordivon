from __future__ import annotations

from domains.decision_intake.models import DecisionIntake

# ── H-5 Alignment ─────────────────────────────────────────────────────────
# TradingDisciplinePolicy flags behavioural red flags as ESCALATE signals
# (not reject). The hard-gate reject decisions for missing fields / limit
# violations are handled directly by RiskEngine.validate_intake().
#
# Rules:
#   is_revenge_trade=true  → escalate (human review required, not auto-reject)
#   is_chasing=true        → escalate (human review required, not auto-reject)
# ───────────────────────────────────────────────────────────────────────────


class TradingDisciplinePolicy:
    """Flags behavioural red flags on finance decision intakes.

    Returns escalate-level reasons only.  Reject-level violations
    (missing fields, risk limits) are handled by RiskEngine.validate_intake().
    """

    def check(self, intake: DecisionIntake) -> list[str]:
        violations: list[str] = []
        payload = intake.payload

        if payload.get("is_revenge_trade") is True:
            violations.append("is_revenge_trade=true — requires human review.")

        if payload.get("is_chasing") is True:
            violations.append("is_chasing=true — requires human review.")

        return violations
