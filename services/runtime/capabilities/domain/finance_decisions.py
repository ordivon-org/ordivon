from __future__ import annotations

from sqlalchemy.orm import Session

from domains.decision_intake.repository import DecisionIntakeRepository
from domains.decision_intake.service import DecisionIntakeService
from governance.audit.auditor import RiskAuditor
from governance.risk_engine.engine import RiskEngine
from packs.finance.decision_intake import validate_finance_decision_intake


class FinanceDecisionCapability:
    abstraction_type = "domain"

    def create_intake(self, payload: dict, db: Session):
        validation_result = validate_finance_decision_intake(payload)
        service = DecisionIntakeService(DecisionIntakeRepository(db))
        return service.record_intake(
            pack_id="finance",
            intake_type="controlled_decision",
            payload=validation_result.payload,
            validation_errors=validation_result.validation_errors,
        )

    def get_intake(self, intake_id: str, db: Session):
        service = DecisionIntakeService(DecisionIntakeRepository(db))
        return service.get_model(intake_id)

    def govern_intake(self, intake_id: str, db: Session):
        """H-5: Run Finance Governance Hard Gate on a DecisionIntake.

        Returns (updated_intake, GovernanceDecision).
        Writes an AuditEvent for the governance evaluation.
        Does NOT create Recommendation, ExecutionReceipt, PlanReceipt, or Outcome.
        """
        service = DecisionIntakeService(DecisionIntakeRepository(db))
        intake = service.get_model(intake_id)

        decision = RiskEngine().validate_intake(intake)

        updated_intake = service.update_governance_status(intake_id, decision.decision)

        # ── Write audit event for governance evaluation only ──────────
        auditor = RiskAuditor()
        auditor.record_event(
            event_type="governance_evaluated",
            entity_type="decision_intake",
            entity_id=intake_id,
            payload={
                "governance_decision": decision.decision,
                "governance_reasons": list(decision.reasons),
                "governance_source": decision.source,
                "governance_policy_set_id": decision.policy_set_id,
                "governance_active_policy_ids": list(decision.active_policy_ids),
            },
            db=db,
        )

        return updated_intake, decision
