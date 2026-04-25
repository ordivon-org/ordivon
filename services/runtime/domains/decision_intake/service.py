from __future__ import annotations

from domains.decision_intake.models import DecisionIntake
from domains.decision_intake.repository import DecisionIntakeRepository
from shared.errors.domain import DomainNotFound


class DecisionIntakeService:
    def __init__(self, repository: DecisionIntakeRepository) -> None:
        self.repository = repository

    def record_intake(
        self,
        *,
        pack_id: str,
        intake_type: str,
        payload: dict,
        validation_errors: list[dict[str, str]],
    ) -> DecisionIntake:
        status = "invalid" if validation_errors else "validated"
        intake = DecisionIntake(
            pack_id=pack_id,
            intake_type=intake_type,
            status=status,
            payload=payload,
            validation_errors=validation_errors,
            governance_status="not_started",
        )
        row = self.repository.create(intake)
        return self.repository.to_model(row)

    def get_model(self, intake_id: str) -> DecisionIntake:
        row = self.repository.get(intake_id)
        if row is None:
            raise DomainNotFound(f"Decision intake not found: {intake_id}")
        return self.repository.to_model(row)

    def update_governance_status(self, intake_id: str, governance_status: str) -> DecisionIntake:
        row = self.repository.update_governance_status(intake_id, governance_status)
        if row is None:
            raise DomainNotFound(f"Decision intake not found: {intake_id}")
        return self.repository.to_model(row)
