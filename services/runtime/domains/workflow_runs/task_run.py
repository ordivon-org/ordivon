from __future__ import annotations

from dataclasses import dataclass, field

from domains.workflow_runs.checkpoint_state import CheckpointState
from domains.workflow_runs.models import WorkflowRun


VALID_TASK_RUN_STATUSES = {"pending", "running", "blocked", "completed", "failed", "cancelled"}


RunCheckpoint = CheckpointState


@dataclass(frozen=True, slots=True)
class TaskRun:
    run_id: str
    task_type: str
    status: str
    trigger: str = "api"
    checkpoint: RunCheckpoint = field(default_factory=RunCheckpoint)

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("TaskRun requires run_id.")
        if not self.task_type:
            raise ValueError("TaskRun requires task_type.")
        if self.status not in VALID_TASK_RUN_STATUSES:
            raise ValueError(f"Unsupported task run status: {self.status}")

    @classmethod
    def from_workflow_run(cls, run: WorkflowRun) -> "TaskRun":
        status_map = {
            "pending": "pending",
            "running": "running",
            "completed": "completed",
            "failed": "failed",
            "cancelled": "cancelled",
        }
        normalized_status = status_map.get(run.status, "running")
        checkpoint = RunCheckpoint.from_workflow_run(run)
        if checkpoint.blocked_reason and normalized_status == "running":
            normalized_status = "blocked"
        return cls(
            run_id=run.id,
            task_type=run.workflow_name,
            status=normalized_status,
            trigger=run.trigger,
            checkpoint=checkpoint,
        )
