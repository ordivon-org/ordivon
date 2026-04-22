from __future__ import annotations

from orchestrator.contracts.handoff import HandoffArtifact
from orchestrator.contracts.workflow import WorkflowContext


def build_handoff_artifact(
    *,
    task_run_id: str,
    root_object_ref: dict[str, str | None],
    blocked_reason: str,
    next_action: str,
    partial_results: dict | None = None,
    evidence_refs: tuple[dict[str, str | None], ...] | None = None,
) -> HandoffArtifact:
    return HandoffArtifact(
        task_run_id=task_run_id,
        root_object_ref=root_object_ref,
        partial_results=dict(partial_results or {}),
        blocked_reason=blocked_reason,
        next_action=next_action,
        evidence_refs=tuple(evidence_refs or ()),
    )


def attach_handoff_artifact(ctx: WorkflowContext, artifact: HandoffArtifact) -> HandoffArtifact:
    ctx.metadata["handoff_artifact"] = artifact.to_payload()
    ctx.metadata["handoff_artifact_ref"] = artifact.id
    ctx.metadata["blocked_reason"] = artifact.blocked_reason
    ctx.metadata["resume_from_ref"] = artifact.id
    return artifact
