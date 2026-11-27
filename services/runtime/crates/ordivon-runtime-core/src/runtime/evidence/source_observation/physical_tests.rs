//! Original Runner source observations are read from actual Attempt files.
//! No assertion depends on which Rust source module implements the contract.
use super::{validate_workspace_source_observation_artifact, SourceObservationRequirement};
use crate::runtime::{AttemptRecord, AttemptState, AttemptTerminationIntent, RuntimeErrorCode};
use crate::universal::{sha256_bytes, RunnerRequest};
use serde_json::json;
use std::fs;

#[test]
fn original_source_observation_matches_the_committed_request_and_real_bytes() {
    let directory = tempfile::tempdir().unwrap();
    let base = directory.path().to_string_lossy().into_owned();
    let launch_token = "original-task-launch-token";
    let committed = format!("sha256:{}", "a".repeat(64));
    let changed = format!("sha256:{}", "b".repeat(64));
    let attempt = AttemptRecord {
        attempt_id: "attempt-source-original".into(),
        job_id: "job-source-original".into(),
        attempt_number: 1,
        state: AttemptState::Starting,
        termination_intent: AttemptTerminationIntent::Natural,
        launch_token_digest: sha256_bytes(launch_token.as_bytes()),
        bundle_path: base.clone(),
        bundle_digest: None,
        boot_id: None,
        unit_name: "ordivon-attempt-source-original.service".into(),
        invocation_id: None,
        control_group: None,
        main_pid: None,
        process_start_identity: None,
        runner_start_digest: None,
        result_digest: None,
        exit_code: None,
        infrastructure_error_digest: None,
        created_at_ms: 1,
        started_at_ms: None,
        finished_at_ms: None,
        row_version: 1,
    };
    let request = json!({
        "schemaVersion": 1,
        "taskId": attempt.attempt_id,
        "jobId": attempt.job_id,
        "attemptId": attempt.attempt_id,
        "launchToken": launch_token,
        "unitName": attempt.unit_name,
        "workspaceId": "ws-source-original",
        "workspacePath": base,
        "workspaceSourceDigest": committed,
        "executable": "/usr/bin/true",
        "executableDigest": format!("sha256:{}", "e".repeat(64)),
        "args": [],
        "cwd": base,
        "env": {},
        "timeoutMs": 1000,
        "stdoutLimitBytes": 4096,
        "stderrLimitBytes": 4096
    });
    let request_bytes = serde_json::to_vec(&request).unwrap();
    let _: RunnerRequest = serde_json::from_slice(&request_bytes)
        .expect("the original native Runner request schema is valid");
    let request_path = directory.path().join("request.json");
    fs::write(&request_path, &request_bytes).unwrap();

    let mut observation = json!({
        "schemaVersion": 1,
        "taskId": attempt.attempt_id,
        "jobId": attempt.job_id,
        "attemptId": attempt.attempt_id,
        "launchTokenDigest": attempt.launch_token_digest,
        "committedWorkspaceSourceDigest": committed,
        "observedWorkspaceSourceDigest": committed,
        "matchesCommitment": true,
        "observedUnixMs": 1234,
    });
    let observation_path = directory.path().join("workspace-source-observation.json");
    let first_bytes = serde_json::to_vec(&observation).unwrap();
    fs::write(&observation_path, &first_bytes).unwrap();
    let artifact = validate_workspace_source_observation_artifact(
        &attempt,
        Some(&committed),
        true,
        SourceObservationRequirement::MustMatch,
    )
    .unwrap()
    .expect("real original observation qualifies an Artifact");
    assert_eq!(artifact.kind, "workspace_source_observation");
    assert_eq!(artifact.digest, sha256_bytes(&first_bytes));
    assert_eq!(artifact.byte_length, first_bytes.len() as u64);

    // A genuine source drift cannot be presented as successful terminal output.
    observation["observedWorkspaceSourceDigest"] = json!(changed);
    observation["matchesCommitment"] = json!(false);
    fs::write(&observation_path, serde_json::to_vec(&observation).unwrap()).unwrap();
    let rejected = validate_workspace_source_observation_artifact(
        &attempt,
        Some(&committed),
        true,
        SourceObservationRequirement::MustMatch,
    )
    .unwrap_err();
    assert_eq!(rejected.code, RuntimeErrorCode::ArtifactIdentityConflict);

    // The very same real bytes are valid evidence of an independently
    // established source-precondition failure, never of a successful process.
    assert!(validate_workspace_source_observation_artifact(
        &attempt,
        Some(&committed),
        true,
        SourceObservationRequirement::MustDiffer,
    )
    .unwrap()
    .is_some());

    // An altered original request cannot make otherwise well-formed result
    // evidence qualify. The actual persisted identity is the test oracle.
    let mut tampered = request.clone();
    tampered["launchToken"] = json!("different-token");
    fs::write(&request_path, serde_json::to_vec(&tampered).unwrap()).unwrap();
    let error = validate_workspace_source_observation_artifact(
        &attempt,
        Some(&committed),
        true,
        SourceObservationRequirement::MustDiffer,
    )
    .unwrap_err();
    assert_eq!(error.code, RuntimeErrorCode::ResultIdentityConflict);
    fs::write(&request_path, request_bytes).unwrap();

    // Missing source observation after an original committed-success claim
    // is not silently accepted.
    fs::remove_file(&observation_path).unwrap();
    let missing = validate_workspace_source_observation_artifact(
        &attempt,
        Some(&committed),
        true,
        SourceObservationRequirement::MustMatch,
    )
    .unwrap_err();
    assert_eq!(missing.code, RuntimeErrorCode::ArtifactIdentityConflict);
}
