from __future__ import annotations

from sqlalchemy.orm import Session

from domains.decision_intake.repository import DecisionIntakeRepository
from domains.decision_intake.service import DecisionIntakeService
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
        service = DecisionIntakeService(DecisionIntakeRepository(db))
        intake = service.get_model(intake_id)
        
        symbol = intake.payload.get("symbol")
        
        from governance.feedback import GovernanceFeedbackReader
        from governance.risk_engine.engine import RiskEngine
        
        hints = GovernanceFeedbackReader(db).list_hints_for_symbol(symbol)
        
        decision = RiskEngine().validate_intake(intake, advisory_hints=hints)
        
        updated_intake = service.update_governance_status(intake_id, decision.decision)
        return updated_intake, decision
