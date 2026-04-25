from __future__ import annotations

from typing import Any

from domains.decision_intake.models import DecisionIntake


class TradingDisciplinePolicy:
    """Enforces strict trading discipline rules on finance decision intakes."""

    def check(self, intake: DecisionIntake) -> list[str]:
        violations = []
        payload = intake.payload

        if payload.get("is_revenge_trade"):
            violations.append("Revenge trading is strictly forbidden.")

        if payload.get("is_chasing"):
            violations.append("Chasing price action is strictly forbidden.")

        emotional_state = (payload.get("emotional_state") or "").lower()
        if "calm" not in emotional_state and "neutral" not in emotional_state:
            violations.append(f"Emotional state must be calm or neutral, got: {emotional_state}")

        confidence = payload.get("confidence")
        if confidence is not None:
            if confidence <= 0.0:
                violations.append("Confidence must be greater than 0.")

        risk_unit = payload.get("risk_unit_usdt")
        max_loss = payload.get("max_loss_usdt")
        if risk_unit and max_loss:
            # Simple check: max loss shouldn't wildly exceed 1 risk unit by default,
            # or maybe max_loss must be > 0 (already handled by validation).
            # Let's enforce max_loss <= 2 * risk_unit as a hard discipline rule.
            if max_loss > 2.0 * risk_unit:
                violations.append(f"Max loss ({max_loss}) exceeds 2x allowed risk unit ({risk_unit}).")

        return violations
