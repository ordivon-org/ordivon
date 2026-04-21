from domains.intelligence_runs.models import IntelligenceRun
from domains.intelligence_runs.repository import IntelligenceRunRepository
from domains.intelligence_runs.state_machine import IntelligenceRunStateMachine
from shared.errors.domain import DomainNotFound


class IntelligenceRunService:
    def __init__(self, repository: IntelligenceRunRepository) -> None:
        self.repository = repository
        self.state_machine = IntelligenceRunStateMachine()

    def create(self, run: IntelligenceRun):
        existing = self.repository.get_by_task_id(run.task_id)
        if existing is not None:
            return existing
        return self.repository.create(run)

    def mark_completed(
        self,
        task_id: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        output_summary: str | None = None,
        started_at: str | None = None,
        completed_at: str | None = None,
    ):
        row = self.repository.get_by_task_id(task_id)
        if row is None:
            raise DomainNotFound(f"Intelligence run not found for task_id: {task_id}")
        self.state_machine.ensure_transition(row.status, "completed")
        return self.repository.update_status(
            task_id,
            status="completed",
            provider=provider,
            model=model,
            output_summary=output_summary,
            started_at=started_at,
            completed_at=completed_at,
        )

    def mark_failed(
        self,
        task_id: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        error: str | None = None,
        started_at: str | None = None,
        completed_at: str | None = None,
    ):
        row = self.repository.get_by_task_id(task_id)
        if row is None:
            raise DomainNotFound(f"Intelligence run not found for task_id: {task_id}")
        self.state_machine.ensure_transition(row.status, "failed")
        return self.repository.update_status(
            task_id,
            status="failed",
            provider=provider,
            model=model,
            error=error,
            started_at=started_at,
            completed_at=completed_at,
        )

    def get_model(self, run_id: str) -> IntelligenceRun | None:
        row = self.repository.get(run_id)
        if row is None:
            return None
        return self.repository.to_model(row)
