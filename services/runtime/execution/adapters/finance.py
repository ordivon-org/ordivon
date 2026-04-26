"""H-6: Finance Plan-Only Receipt Adapter.

Thin execution adapter for creating plan-only receipts from
finance decision intakes that have passed governance (execute).

This adapter:
- Creates an ExecutionRequest + ExecutionReceipt
- Records a plan_receipt_created AuditEvent
- Does NOT connect to any broker, exchange, order, or trade system

receipt_kind = "plan"
broker_execution = false
side_effect_level = "none"
"""

from __future__ import annotations

from dataclasses import dataclass

from capabilities.boundary import ActionContext
from domains.execution_records.repository import ExecutionRecordRepository
from domains.execution_records.service import ExecutionRecordService
from governance.audit.auditor import RiskAuditor


@dataclass(slots=True)
class FinancePlanReceiptResult:
    execution_request_id: str
    execution_receipt_id: str
    receipt_kind: str
    broker_execution: bool
    side_effect_level: str
    decision_intake_id: str
    governance_status: str


class FinancePlanReceiptAdapter:
    """Creates plan-only receipts for finance decision intakes."""

    family_name = "finance"

    def __init__(self, db, auditor: RiskAuditor | None = None) -> None:
        self.db = db
        self.execution_service = ExecutionRecordService(ExecutionRecordRepository(db))
        self.auditor = auditor or RiskAuditor()

    def create_plan_receipt(
        self,
        *,
        action_context: ActionContext,
        decision_intake_id: str,
        governance_status: str,
    ) -> FinancePlanReceiptResult:
        # ── 1. Create execution request ──────────────────────────────
        request_row = self.execution_service.start_request(
            action_id="finance_decision_plan",
            action_context=action_context,
            payload={
                "receipt_kind": "plan",
                "broker_execution": False,
                "side_effect_level": "none",
                "decision_intake_id": decision_intake_id,
                "governance_status": governance_status,
            },
            entity_type="decision_intake",
            entity_id=decision_intake_id,
        )

        # ── 2. Create success receipt ────────────────────────────────
        receipt_row = self.execution_service.record_success(
            request_row.id,
            detail={
                "receipt_kind": "plan",
                "broker_execution": False,
                "side_effect_level": "none",
                "decision_intake_id": decision_intake_id,
                "governance_status": governance_status,
            },
        )

        # ── 3. Write audit event ─────────────────────────────────────
        self.auditor.record_event(
            event_type="plan_receipt_created",
            entity_type="decision_intake",
            entity_id=decision_intake_id,
            payload={
                "decision": "logged",
                "source": "finance_decision.plan_only_receipt",
                "execution_request_id": request_row.id,
                "execution_receipt_id": receipt_row.id,
                "receipt_kind": "plan",
                "broker_execution": False,
                "side_effect_level": "none",
                "decision_intake_id": decision_intake_id,
                "governance_status": governance_status,
            },
            db=self.db,
        )

        return FinancePlanReceiptResult(
            execution_request_id=request_row.id,
            execution_receipt_id=receipt_row.id,
            receipt_kind="plan",
            broker_execution=False,
            side_effect_level="none",
            decision_intake_id=decision_intake_id,
            governance_status=governance_status,
        )
