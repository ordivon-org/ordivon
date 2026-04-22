from orchestrator.contracts.handoff import HandoffArtifact


def test_handoff_artifact_payload_contains_formal_refs():
    artifact = HandoffArtifact(
        task_run_id="wfrun_1",
        root_object_ref={"object_type": "analysis", "object_id": "analysis_1"},
        partial_results={"decision": "escalate"},
        blocked_reason="approval_required",
        next_action="human_review",
        evidence_refs=({"object_type": "policy", "object_id": "policy_1"},),
    )

    payload = artifact.to_payload()

    assert payload["task_run_id"] == "wfrun_1"
    assert payload["root_object_ref"]["object_type"] == "analysis"
    assert payload["blocked_reason"] == "approval_required"
    assert payload["next_action"] == "human_review"
