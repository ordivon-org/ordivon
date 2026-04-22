from __future__ import annotations

from dataclasses import dataclass

from domains.workflow_runs.models import WorkflowRun


@dataclass(frozen=True, slots=True)
class CheckpointState:
    blocked_reason: str | None = None
    wake_reason: str | None = None
    resume_marker: str | None = None
    handoff_artifact_ref: str | None = None
    resume_from_ref: str | None = None
    resume_reason: str | None = None
    resume_count: int = 0

    @classmethod
    def from_workflow_run(cls, run: WorkflowRun) -> "CheckpointState":
        return cls(
            blocked_reason=run.blocked_reason,
            wake_reason=run.wake_reason,
            resume_marker=run.resume_marker,
            handoff_artifact_ref=run.handoff_artifact_ref,
            resume_from_ref=run.resume_from_ref,
            resume_reason=run.resume_reason,
            resume_count=run.resume_count,
        )

    def to_lineage_refs(self, lineage_refs: dict[str, object] | None = None) -> dict[str, object]:
        payload = dict(lineage_refs or {})
        if self.blocked_reason is not None:
            payload["blocked_reason"] = self.blocked_reason
        if self.wake_reason is not None:
            payload["wake_reason"] = self.wake_reason
        if self.resume_marker is not None:
            payload["resume_marker"] = self.resume_marker
        if self.handoff_artifact_ref is not None:
            payload["handoff_artifact_ref"] = self.handoff_artifact_ref
        if self.resume_from_ref is not None:
            payload["resume_from_ref"] = self.resume_from_ref
        if self.resume_reason is not None:
            payload["resume_reason"] = self.resume_reason
        if self.resume_count:
            payload["resume_count"] = self.resume_count
        return payload
