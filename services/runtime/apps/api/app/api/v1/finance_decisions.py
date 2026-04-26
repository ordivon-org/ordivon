from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.app.deps import get_db
from apps.api.app.schemas.finance_decisions import (
    FinanceDecisionIntakeRequest,
    FinanceDecisionIntakeResponse,
    FinanceManualOutcomeRequest,
    FinanceManualOutcomeResponse,
    FinancePlanReceiptResponse,
)
from capabilities.domain.finance_decisions import (
    FinanceDecisionCapability,
    PlanReceiptConflict,
    PlanReceiptNotAllowed,
)
from capabilities.domain.finance_outcome import (
    DecisionIntakeNotFound,
    FinanceOutcomeCapability,
    ManualOutcomeConflict,
    PlanReceiptNotValid,
)

router = APIRouter()
finance_decision_capability = FinanceDecisionCapability()
finance_outcome_capability = FinanceOutcomeCapability()


@router.post("/finance-decisions/intake", response_model=FinanceDecisionIntakeResponse)
async def create_finance_decision_intake(
    payload: FinanceDecisionIntakeRequest, db: Session = Depends(get_db)
) -> FinanceDecisionIntakeResponse:
    try:
        model = finance_decision_capability.create_intake(payload.model_dump(), db)
        db.commit()
        return FinanceDecisionIntakeResponse(
            id=model.id,
            pack_id=model.pack_id,
            intake_type=model.intake_type,
            status=model.status,
            payload=model.payload,
            validation_errors=model.validation_errors,
            governance_status=model.governance_status,
            created_at=model.created_at,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/finance-decisions/intake/{intake_id}", response_model=FinanceDecisionIntakeResponse)
async def get_finance_decision_intake(
    intake_id: str, db: Session = Depends(get_db)
) -> FinanceDecisionIntakeResponse:
    from shared.errors.domain import DomainNotFound
    try:
        model = finance_decision_capability.get_intake(intake_id, db)
        return FinanceDecisionIntakeResponse(
            id=model.id,
            pack_id=model.pack_id,
            intake_type=model.intake_type,
            status=model.status,
            payload=model.payload,
            validation_errors=model.validation_errors,
            governance_status=model.governance_status,
            created_at=model.created_at,
        )
    except DomainNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── H-6: Plan-Only Receipt ────────────────────────────────────────────────

@router.post(
    "/finance-decisions/intake/{intake_id}/plan",
    response_model=FinancePlanReceiptResponse,
)
async def create_finance_decision_plan_receipt(
    intake_id: str, db: Session = Depends(get_db)
) -> FinancePlanReceiptResponse:
    """H-6: Create a plan-only receipt for a governed intake.

    Requires governance_status == \"execute\".
    Rejects invalid, rejected, escalated, or duplicate intakes.
    Does NOT connect to broker, exchange, order, or trade systems.
    """
    try:
        result = finance_decision_capability.plan_intake(intake_id, db)
        db.commit()
        return FinancePlanReceiptResponse(
            execution_request_id=result.execution_request_id,
            execution_receipt_id=result.execution_receipt_id,
            receipt_kind=result.receipt_kind,
            broker_execution=result.broker_execution,
            side_effect_level=result.side_effect_level,
            decision_intake_id=result.decision_intake_id,
            governance_status=result.governance_status,
        )
    except PlanReceiptNotAllowed as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except PlanReceiptConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── H-7: Manual Outcome Capture ──────────────────────────────────────


@router.post(
    "/finance-decisions/intake/{intake_id}/outcome",
    response_model=FinanceManualOutcomeResponse,
)
async def capture_manual_outcome(
    intake_id: str,
    payload: FinanceManualOutcomeRequest,
    db: Session = Depends(get_db),
) -> FinanceManualOutcomeResponse:
    """H-7: Capture manual outcome for a governed, plan-receipted intake.

    Validates the plan receipt is valid (H-6 gate).
    Rejects duplicate outcomes (409).
    Does NOT connect to broker, exchange, order, or trade systems.
    Does NOT auto-create Review, CandidateRule, or Policy changes.
    """
    try:
        result = finance_outcome_capability.capture_manual_outcome(
            decision_intake_id=intake_id,
            execution_receipt_id=payload.execution_receipt_id,
            observed_outcome=payload.observed_outcome,
            verdict=payload.verdict,
            variance_summary=payload.variance_summary,
            plan_followed=payload.plan_followed,
            db=db,
        )
        db.commit()
        return FinanceManualOutcomeResponse(
            outcome_id=result.outcome_id,
            decision_intake_id=result.decision_intake_id,
            execution_receipt_id=result.execution_receipt_id,
            outcome_source=result.outcome_source,
            observed_outcome=result.observed_outcome,
            verdict=result.verdict,
            variance_summary=result.variance_summary,
            plan_followed=result.plan_followed,
            created_at=result.created_at,
        )
    except ManualOutcomeConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except PlanReceiptNotValid as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except DecisionIntakeNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/finance-decisions/intake/{intake_id}/govern", response_model=FinanceDecisionIntakeResponse)
async def govern_finance_decision_intake(
    intake_id: str, db: Session = Depends(get_db)
) -> FinanceDecisionIntakeResponse:
    from shared.errors.domain import DomainNotFound
    try:
        model, decision = finance_decision_capability.govern_intake(intake_id, db)
        db.commit()
        return FinanceDecisionIntakeResponse(
            id=model.id,
            pack_id=model.pack_id,
            intake_type=model.intake_type,
            status=model.status,
            payload=model.payload,
            validation_errors=model.validation_errors,
            governance_status=model.governance_status,
            governance_decision=decision.decision,
            governance_reasons=list(decision.reasons),
            governance_policy_refs=list(decision.active_policy_ids),
            advisory_hints=[hint.to_payload() for hint in decision.advisory_hints],
            created_at=model.created_at,
        )
    except DomainNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
