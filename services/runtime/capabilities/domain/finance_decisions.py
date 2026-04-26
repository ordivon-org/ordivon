from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from capabilities.boundary import build_action_context
from domains.decision_intake.repository import DecisionIntakeRepository
from domains.decision_intake.service import DecisionIntakeService
from domains.execution_records.repository import ExecutionRecordRepository
from execution.adapters.finance import FinancePlanReceiptAdapter, FinancePlanReceiptResult
from governance.audit.auditor import RiskAuditor
from governance.risk_engine.engine import RiskEngine
from packs.finance.decision_intake import validate_finance_decision_intake


class PlanReceiptConflict(Exception):
    """A plan receipt for this intake already exists (idempotency guard)."""
    def __init__(self, intake_id: str, existing_request_id: str):
        self.intake_id = intake_id
        self.existing_request_id = existing_request_id
        super().__init__(
            f"Plan receipt already exists for intake {intake_id} "
            f"(execution request {existing_request_id})."
        )


class PlanReceiptNotAllowed(Exception):
    """Governance status does not allow plan receipt creation."""
    def __init__(self, intake_id: str, governance_status: str):
        self.intake_id = intake_id
        self.governance_status = governance_status
        super().__init__(
            f"Plan receipt requires governance_status=execute, "
            f"got '{governance_status}' for intake {intake_id}."
        )


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

    def plan_intake(self, intake_id: str, db: Session) -> FinancePlanReceiptResult:
        """H-6: Create a plan-only receipt for a governed intake.

        Requires governance_status == "execute".
        Rejects duplicate plan creation (409 conflict).
        Writes a plan_receipt_created AuditEvent.
        Does NOT connect to broker, exchange, order, or trade systems.
        """
        service = DecisionIntakeService(DecisionIntakeRepository(db))
        intake = service.get_model(intake_id)

        # ── Gate: only execute governance ────────────────────────────
        if intake.governance_status != "execute":
            raise PlanReceiptNotAllowed(intake_id, intake.governance_status)

        # ── Gate: idempotency — reject duplicate ─────────────────────
        idempotency_key = f"{intake_id}-plan"
        exec_repo = ExecutionRecordRepository(db)
        existing = exec_repo.get_request_by_idempotency_key(idempotency_key)
        if existing is not None:
            raise PlanReceiptConflict(intake_id, existing.id)

        # ── Create plan receipt via adapter ──────────────────────────
        action_context = build_action_context(
            action="finance_decision_plan",
            actor="pfios.finance_decision.govern_hard_gate",
            context=f"decision_intake:{intake_id}",
            reason="Governance hard gate returned execute — creating plan-only receipt.",
            idempotency_key=idempotency_key,
        )

        adapter = FinancePlanReceiptAdapter(db)
        return adapter.create_plan_receipt(
            action_context=action_context,
            decision_intake_id=intake_id,
            governance_status=intake.governance_status,
        )
