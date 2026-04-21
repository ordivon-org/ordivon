from __future__ import annotations

from domains.workflow_runs.models import WorkflowRun
from domains.workflow_runs.repository import WorkflowRunRepository


class WorkflowRunService:
    def __init__(self, repository: WorkflowRunRepository) -> None:
        self.repository = repository

    def create(self, run: WorkflowRun):
        return self.repository.create(run)

    def save(self, run: WorkflowRun):
        return self.repository.upsert(run)

    def get_model(self, run_id: str) -> WorkflowRun | None:
        row = self.repository.get(run_id)
        if row is None:
            return None
        return self.repository.to_model(row)
