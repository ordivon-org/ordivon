"""H-7: Finance Manual Outcome Capture Capability.

Domain capability for capturing manual outcomes against finance decision
intakes that have been planned (H-6 plan-only receipt).

This capability:
- Validates the plan receipt exists and is valid (H-6 gate)
- Enforces one-outcome-per-intake (409 conflict)
- Persists a FinanceManualOutcome
- Records an outcome_captured AuditEvent
- Does NOT connect to broker, exchange, order, or trade systems
- Does NOT auto-create Review, CandidateRule, or Policy changes
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from domains.decision_intake.repository import DecisionIntakeRepository
from domains.decision_intake.service import DecisionIntakeService
from domains.execution_records.repository import ExecutionRecordRepository
from domains.finance_outcome.models import FinanceManualOutcome
from domains.finance_outcome.repository import FinanceManualOutcomeRepository
from governance_engine.audit.auditor import RiskAuditor


class PlanReceiptNotValid(Exception):
    """The referenced plan receipt does not meet all validation criteria."""

    def __init__(self, execution_receipt_id: str, reason: str):
        self.execution_receipt_id = execution_receipt_id
        self.reason = reason
        super().__init__(f"Plan receipt {execution_receipt_id} is not valid: {reason}")


class ManualOutcomeConflict(Exception):
    """An outcome already exists for this decision intake."""

    def __init__(self, decision_intake_id: str, existing_outcome_id: str):
        self.decision_intake_id = decision_intake_id
        self.existing_outcome_id = existing_outcome_id
        super().__init__(
            f"Manual outcome already exists for intake {decision_intake_id} (existing outcome: {existing_outcome_id})."
        )


class DecisionIntakeNotFound(Exception):
    """The referenced decision intake does not exist."""

    def __init__(self, decision_intake_id: str):
        self.decision_intake_id = decision_intake_id
        super().__init__(f"Decision intake not found: {decision_intake_id}")


@dataclass(slots=True)
class FinanceManualOutcomeResult:
    outcome_id: str
    decision_intake_id: str
    execution_receipt_id: str
    outcome_source: str
    observed_outcome: str
    verdict: str
    variance_summary: str | None
    plan_followed: bool
    created_at: str


class FinanceOutcomeCapability:
    abstraction_type = "domain"

    def capture_manual_outcome(
        self,
        *,
        decision_intake_id: str,
        execution_receipt_id: str,
        observed_outcome: str,
        verdict: str,
        variance_summary: str | None = None,
        plan_followed: bool = False,
        db: Session,
    ) -> FinanceManualOutcomeResult:
        # ── 1. Verify decision intake exists ─────────────────────────
        intake_service = DecisionIntakeService(DecisionIntakeRepository(db))
        try:
            intake_service.get_model(decision_intake_id)
        except Exception as exc:
            if "not found" in str(exc).lower():
                raise DecisionIntakeNotFound(decision_intake_id) from exc
            raise

        # ── 2. Validate the plan receipt ─────────────────────────────
        exec_repo = ExecutionRecordRepository(db)
        receipt_row = exec_repo.get_receipt(execution_receipt_id)
        if receipt_row is None:
            raise PlanReceiptNotValid(
                execution_receipt_id,
                "Execution receipt not found.",
            )
        receipt = exec_repo.to_receipt_model(receipt_row)

        # Gate: receipt must be succeeded
        if receipt.status != "succeeded":
            raise PlanReceiptNotValid(
                execution_receipt_id,
                f"Receipt status is '{receipt.status}', expected 'succeeded'.",
            )

        # Gate: receipt must be for finance_decision_plan
        if receipt.action_id != "finance_decision_plan":
            raise PlanReceiptNotValid(
                execution_receipt_id,
                f"Receipt action_id is '{receipt.action_id}', expected 'finance_decision_plan'.",
            )

        # Gate: detail must contain plan-only metadata
        detail = receipt.detail

        if detail.get("receipt_kind") != "plan":
            raise PlanReceiptNotValid(
                execution_receipt_id,
                f"receipt_kind is '{detail.get('receipt_kind')}', expected 'plan'.",
            )

        if detail.get("broker_execution") is not False:
            raise PlanReceiptNotValid(
                execution_receipt_id,
                "broker_execution is not false — not a plan-only receipt.",
            )

        if detail.get("side_effect_level") != "none":
            raise PlanReceiptNotValid(
                execution_receipt_id,
                f"side_effect_level is '{detail.get('side_effect_level')}', expected 'none'.",
            )

        # Gate: decision_intake_id in detail must match path intake_id
        if detail.get("decision_intake_id") != decision_intake_id:
            raise PlanReceiptNotValid(
                execution_receipt_id,
                f"decision_intake_id in receipt detail "
                f"('{detail.get('decision_intake_id')}') "
                f"does not match path intake_id ('{decision_intake_id}').",
            )

        # ── 3. Check for duplicate outcome ───────────────────────────
        outcome_repo = FinanceManualOutcomeRepository(db)
        existing = outcome_repo.find_for_intake(decision_intake_id)
        if existing is not None:
            raise ManualOutcomeConflict(decision_intake_id, existing.id)

        # ── 4. Create outcome ────────────────────────────────────────
        outcome = FinanceManualOutcome(
            decision_intake_id=decision_intake_id,
            execution_receipt_id=execution_receipt_id,
            outcome_source="manual",
            observed_outcome=observed_outcome,
            verdict=verdict,
            variance_summary=variance_summary,
            plan_followed=plan_followed,
        )
        row = outcome_repo.create(outcome)

        # ── 5. Write audit event ─────────────────────────────────────
        auditor = RiskAuditor()
        auditor.record_event(
            event_type="outcome_captured",
            entity_type="decision_intake",
            entity_id=decision_intake_id,
            payload={
                "outcome_id": row.id,
                "decision_intake_id": decision_intake_id,
                "execution_receipt_id": execution_receipt_id,
                "outcome_source": "manual",
                "observed_outcome": observed_outcome,
                "verdict": verdict,
                "variance_summary": variance_summary,
                "plan_followed": plan_followed,
            },
            db=db,
        )

        return FinanceManualOutcomeResult(
            outcome_id=row.id,
            decision_intake_id=decision_intake_id,
            execution_receipt_id=execution_receipt_id,
            outcome_source="manual",
            observed_outcome=observed_outcome,
            verdict=verdict,
            variance_summary=variance_summary,
            plan_followed=plan_followed,
            created_at=row.created_at.isoformat(),
        )
