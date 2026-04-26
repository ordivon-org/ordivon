from sqlalchemy.orm import Session

from domains.finance_outcome.models import FinanceManualOutcome
from domains.finance_outcome.orm import FinanceManualOutcomeORM


class FinanceManualOutcomeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, outcome: FinanceManualOutcome) -> FinanceManualOutcomeORM:
        row = FinanceManualOutcomeORM(
            id=outcome.id,
            decision_intake_id=outcome.decision_intake_id,
            execution_receipt_id=outcome.execution_receipt_id,
            outcome_source=outcome.outcome_source,
            observed_outcome=outcome.observed_outcome,
            verdict=outcome.verdict,
            variance_summary=outcome.variance_summary,
            plan_followed=outcome.plan_followed,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def get(self, outcome_id: str) -> FinanceManualOutcomeORM | None:
        return self.db.get(FinanceManualOutcomeORM, outcome_id)

    def find_for_intake(self, decision_intake_id: str) -> FinanceManualOutcomeORM | None:
        return (
            self.db.query(FinanceManualOutcomeORM)
            .filter(FinanceManualOutcomeORM.decision_intake_id == decision_intake_id)
            .order_by(FinanceManualOutcomeORM.created_at.desc())
            .first()
        )

    def to_model(self, row: FinanceManualOutcomeORM) -> FinanceManualOutcome:
        return FinanceManualOutcome(
            id=row.id,
            decision_intake_id=row.decision_intake_id,
            execution_receipt_id=row.execution_receipt_id,
            outcome_source=row.outcome_source,
            observed_outcome=row.observed_outcome,
            verdict=row.verdict,
            variance_summary=row.variance_summary,
            plan_followed=row.plan_followed,
            created_at=row.created_at.isoformat(),
        )
