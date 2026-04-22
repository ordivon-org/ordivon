from domains.workflow_runs.checkpoint_state import CheckpointState
from domains.workflow_runs.models import WorkflowRun


def test_checkpoint_state_round_trips_handoff_and_resume_fields():
    run = WorkflowRun(
        id="wfrun_1",
        workflow_name="analyze",
        lineage_refs={
            "blocked_reason": "approval_required",
            "wake_reason": "runtime_recovered_later",
            "resume_marker": "handoff:handoff_1",
            "handoff_artifact_ref": "handoff_1",
            "resume_from_ref": "handoff_1",
            "resume_reason": "fallback_path_completed",
            "resume_count": 2,
        },
    )

    checkpoint = CheckpointState.from_workflow_run(run)

    assert checkpoint.blocked_reason == "approval_required"
    assert checkpoint.handoff_artifact_ref == "handoff_1"
    assert checkpoint.resume_reason == "fallback_path_completed"
    assert checkpoint.to_lineage_refs({})["resume_count"] == 2
