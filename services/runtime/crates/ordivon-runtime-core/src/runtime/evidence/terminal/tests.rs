use super::prepare_runner_terminal_from_bundle;
use crate::runtime::{AttemptRecord, AttemptState, AttemptTerminationIntent};
use crate::universal::sha256_bytes;
use serde_json::{json, Value};
use std::fs;

fn admitted_windows_attempt(directory: &std::path::Path) -> AttemptRecord {
    AttemptRecord {
        attempt_id: "attempt-windows-pg-contract".into(),
        job_id: "job-windows-pg-contract".into(),
        attempt_number: 1,
        state: AttemptState::Starting,
        termination_intent: AttemptTerminationIntent::Natural,
        launch_token_digest: sha256_bytes(b"original-one-shot-launch-token"),
        bundle_path: directory.to_string_lossy().into_owned(),
        bundle_digest: Some(sha256_bytes(b"frozen-windows-request")),
        boot_id: None,
        unit_name: "Ordivon.attempt-windows-pg-contract".into(),
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
    }
}

fn native_launcher_result(attempt: &AttemptRecord, stdout: &[u8]) -> Value {
    // Exact JSON key/shape contract emitted by Ordivon.WindowsJobLauncher.cs
    // WriteRuntimeResult (not the PG Runner's Linux-only process format).
    json!({
        "schemaVersion": 1,
        "taskId": attempt.attempt_id,
        "jobId": attempt.job_id,
        "attemptId": attempt.attempt_id,
        "launchTokenDigest": attempt.launch_token_digest,
        "status": "COMPLETED",
        "exitCode": 0,
        "timedOut": false,
        "startedUnixMs": 1000,
        "finishedUnixMs": 1001,
        "steps": [{
            "id": "command", "index": 0, "status": "succeeded",
            "exitCode": 0, "timedOut": false, "continued": false,
            "startedUnixMs": 1000, "finishedUnixMs": 1001
        }],
        "stdout": {
            "artifactId": format!("{}.stdout", attempt.attempt_id),
            "fileName": "stdout.log", "digest": sha256_bytes(stdout),
            "retainedBytes": stdout.len(), "droppedBytes": 0, "truncated": false
        },
        "stderr": {
            "artifactId": format!("{}.stderr", attempt.attempt_id),
            "fileName": "stderr.log", "digest": sha256_bytes(b""),
            "retainedBytes": 0, "droppedBytes": 0, "truncated": false
        }
    })
}

#[test]
fn payload_identity_requires_exact_original_committed_request_not_result_claims() {
    let directory = tempfile::tempdir().unwrap();
    let mut attempt = admitted_windows_attempt(directory.path());
    let stdout = b"original nonroot task bytes\n";
    fs::write(directory.path().join("stdout.log"), stdout).unwrap();
    fs::write(directory.path().join("stderr.log"), b"").unwrap();
    let root = directory.path().to_string_lossy().into_owned();
    let mut request = json!({
        "schemaVersion": 1,
        "jobId": attempt.job_id,
        "attemptId": attempt.attempt_id,
        "taskId": attempt.attempt_id,
        "launchToken": "original-one-shot-launch-token",
        "unitName": attempt.unit_name,
        "workspaceId": "original-ws",
        "workspacePath": root,
        "executable": "/usr/bin/true",
        "executableDigest": sha256_bytes(b"example-executable"),
        "args": [],
        "cwd": root,
        "env": {},
        "timeoutMs": 1000,
        "stdoutLimitBytes": 4096,
        "stderrLimitBytes": 4096,
        "payload": {
            "uid": 65534, "gid": 65534,
            "workspaceView": root, "cwdView": root,
            "runtimeView": root, "cacheView": root
        }
    });
    let request_bytes = serde_json::to_vec(&request).unwrap();
    let _: crate::universal::RunnerRequest =
        serde_json::from_slice(&request_bytes).expect("real Runner request schema");
    attempt.bundle_digest = Some(sha256_bytes(&request_bytes));
    let request_path = directory.path().join("request.json");
    fs::write(&request_path, &request_bytes).unwrap();
    let mut result = native_launcher_result(&attempt, stdout);
    result["payloadUid"] = json!(65534);
    result["payloadGid"] = json!(65534);
    let result_path = directory.path().join("result.json");
    fs::write(&result_path, serde_json::to_vec(&result).unwrap()).unwrap();
    let committed = prepare_runner_terminal_from_bundle(&attempt)
        .expect("same original PG committed nonroot identity");
    assert_eq!(committed.state, AttemptState::Succeeded);

    for (uid, gid) in [
        (json!(null), json!(null)),
        (json!(0), json!(65534)),
        (json!(65534), json!(0)),
        (json!(65534), json!(65535)),
    ] {
        result["payloadUid"] = uid;
        result["payloadGid"] = gid;
        fs::write(&result_path, serde_json::to_vec(&result).unwrap()).unwrap();
        let err = prepare_runner_terminal_from_bundle(&attempt).unwrap_err();
        assert_eq!(
            err.code,
            crate::runtime::RuntimeErrorCode::ResultIdentityConflict
        );
    }
    result["payloadUid"] = json!(65534);
    result["payloadGid"] = json!(65534);
    fs::write(&result_path, serde_json::to_vec(&result).unwrap()).unwrap();
    request["payload"]["uid"] = json!(0);
    fs::write(&request_path, serde_json::to_vec(&request).unwrap()).unwrap();
    let err = prepare_runner_terminal_from_bundle(&attempt).unwrap_err();
    assert_eq!(
        err.code,
        crate::runtime::RuntimeErrorCode::ResultIdentityConflict
    );
    fs::remove_file(&request_path).unwrap();
    let err = prepare_runner_terminal_from_bundle(&attempt).unwrap_err();
    assert_eq!(
        err.code,
        crate::runtime::RuntimeErrorCode::ResultIdentityConflict
    );
}

#[test]
fn original_windows_launcher_result_is_accepted_by_existing_pg_terminal_parser() {
    let directory = tempfile::tempdir().unwrap();
    let attempt = admitted_windows_attempt(directory.path());
    let stdout = b"WINPG_NATIVE_POSTGRES_REAL_RESULT_R7\r\n";
    fs::write(directory.path().join("stdout.log"), stdout).unwrap();
    fs::write(directory.path().join("stderr.log"), b"").unwrap();
    let result = native_launcher_result(&attempt, stdout);
    fs::write(
        directory.path().join("result.json"),
        serde_json::to_vec(&result).unwrap(),
    )
    .unwrap();

    let terminal = prepare_runner_terminal_from_bundle(&attempt).unwrap();
    assert_eq!(terminal.state, AttemptState::Succeeded);
    assert_eq!(terminal.reason_code, "PROCESS_EXIT_ZERO");
    assert_eq!(terminal.exit_code, Some(0));
    assert_eq!(terminal.artifacts.len(), 3);
    assert_eq!(terminal.artifacts[0].kind, "stdout");
    assert_eq!(terminal.artifacts[0].digest, sha256_bytes(stdout));
    assert_eq!(terminal.artifacts[0].relative_path, "sealed-stdout.log");
    assert_eq!(terminal.artifacts[1].relative_path, "sealed-stderr.log");
    assert_eq!(
        fs::read(directory.path().join("sealed-stdout.log")).unwrap(),
        stdout
    );
    assert_eq!(
        fs::read(directory.path().join("sealed-stderr.log")).unwrap(),
        b""
    );
    assert_eq!(terminal.artifacts[2].kind, "execution_result");
}

#[test]
fn terminal_artifact_keeps_committed_bytes_after_original_log_appends() {
    // The native Runner may have produced a correct terminal receipt, but
    // the original log pathname is still writeable by a delayed producer.
    // Consumers need stable registered Artifact bytes, not a mutable tail.
    let directory = tempfile::tempdir().unwrap();
    let attempt = admitted_windows_attempt(directory.path());
    let stdout = b"original committed output\n";
    fs::write(directory.path().join("stdout.log"), stdout).unwrap();
    fs::write(directory.path().join("stderr.log"), b"").unwrap();
    fs::write(
        directory.path().join("result.json"),
        serde_json::to_vec(&native_launcher_result(&attempt, stdout)).unwrap(),
    )
    .unwrap();
    let terminal = prepare_runner_terminal_from_bundle(&attempt).unwrap();
    let registered_stdout = &terminal.artifacts[0];
    assert_ne!(registered_stdout.relative_path, "stdout.log");
    assert_eq!(registered_stdout.digest, sha256_bytes(stdout));
    fs::write(
        directory.path().join("stdout.log"),
        b"original committed output\nlate append not part of registered output\n",
    )
    .unwrap();
    assert_eq!(
        fs::read(directory.path().join(&registered_stdout.relative_path)).unwrap(),
        stdout
    );
    assert_eq!(
        sha256_bytes(&fs::read(directory.path().join(&registered_stdout.relative_path)).unwrap()),
        registered_stdout.digest
    );
    assert!(prepare_runner_terminal_from_bundle(&attempt).is_err());
}

#[test]
fn terminal_artifact_refuses_to_reseal_a_different_preexisting_snapshot() {
    let directory = tempfile::tempdir().unwrap();
    let attempt = admitted_windows_attempt(directory.path());
    let stdout = b"committed bytes\n";
    fs::write(directory.path().join("stdout.log"), stdout).unwrap();
    fs::write(directory.path().join("stderr.log"), b"").unwrap();
    fs::write(
        directory.path().join("result.json"),
        serde_json::to_vec(&native_launcher_result(&attempt, stdout)).unwrap(),
    )
    .unwrap();
    let first = prepare_runner_terminal_from_bundle(&attempt).unwrap();
    assert_eq!(first.artifacts[0].relative_path, "sealed-stdout.log");
    let replay = prepare_runner_terminal_from_bundle(&attempt).unwrap();
    assert_eq!(first.artifacts[0].digest, replay.artifacts[0].digest);
    assert_eq!(
        first.artifacts[0].relative_path,
        replay.artifacts[0].relative_path
    );

    fs::write(
        directory.path().join("sealed-stdout.log"),
        b"corrupted after publish",
    )
    .unwrap();
    let error = prepare_runner_terminal_from_bundle(&attempt).unwrap_err();
    assert_eq!(
        error.code,
        crate::runtime::RuntimeErrorCode::ArtifactIdentityConflict
    );
    assert_eq!(
        fs::read(directory.path().join("sealed-stdout.log")).unwrap(),
        b"corrupted after publish",
        "no implicit digest rewrite, reseal or repair of a committed Artifact"
    );
}

#[cfg(unix)]
#[test]
fn terminal_artifact_does_not_adopt_symlinked_seal_path() {
    let directory = tempfile::tempdir().unwrap();
    let attempt = admitted_windows_attempt(directory.path());
    let stdout = b"immutable output\n";
    fs::write(directory.path().join("stdout.log"), stdout).unwrap();
    fs::write(directory.path().join("stderr.log"), b"").unwrap();
    fs::write(
        directory.path().join("result.json"),
        serde_json::to_vec(&native_launcher_result(&attempt, stdout)).unwrap(),
    )
    .unwrap();
    std::os::unix::fs::symlink(
        directory.path().join("stdout.log"),
        directory.path().join("sealed-stdout.log"),
    )
    .unwrap();
    let error = prepare_runner_terminal_from_bundle(&attempt).unwrap_err();
    assert_eq!(
        error.code,
        crate::runtime::RuntimeErrorCode::ArtifactIdentityConflict
    );
    assert_eq!(
        fs::read(directory.path().join("stdout.log")).unwrap(),
        stdout,
    );
}

#[test]
fn original_windows_result_identity_and_artifact_mutation_fail_closed() {
    let directory = tempfile::tempdir().unwrap();
    let attempt = admitted_windows_attempt(directory.path());
    let stdout = b"WINPG_NATIVE_POSTGRES_REAL_RESULT_R7\r\n";
    fs::write(directory.path().join("stdout.log"), stdout).unwrap();
    fs::write(directory.path().join("stderr.log"), b"").unwrap();
    let mut result = native_launcher_result(&attempt, stdout);
    let path = directory.path().join("result.json");
    fs::write(&path, serde_json::to_vec(&result).unwrap()).unwrap();
    assert!(prepare_runner_terminal_from_bundle(&attempt).is_ok());

    fs::write(directory.path().join("stdout.log"), b"tampered").unwrap();
    assert!(prepare_runner_terminal_from_bundle(&attempt).is_err());
    fs::write(directory.path().join("stdout.log"), stdout).unwrap();

    result["launchTokenDigest"] = json!(sha256_bytes(b"unadmitted-launch-token"));
    fs::write(&path, serde_json::to_vec(&result).unwrap()).unwrap();
    assert!(prepare_runner_terminal_from_bundle(&attempt).is_err());
}

#[test]
fn original_result_rejects_same_size_mutated_stdout_before_sealing() {
    let directory = tempfile::tempdir().unwrap();
    let attempt = admitted_windows_attempt(directory.path());
    let committed = b"good-output!\n";
    let altered = b"evil-output!\n";
    assert_eq!(
        committed.len(),
        altered.len(),
        "this checks bytes, not length"
    );
    fs::write(directory.path().join("stdout.log"), altered).unwrap();
    fs::write(directory.path().join("stderr.log"), b"").unwrap();
    fs::write(
        directory.path().join("result.json"),
        serde_json::to_vec(&native_launcher_result(&attempt, committed)).unwrap(),
    )
    .unwrap();
    let rejected = prepare_runner_terminal_from_bundle(&attempt).unwrap_err();
    assert_eq!(
        rejected.code,
        crate::runtime::RuntimeErrorCode::ArtifactIdentityConflict,
        "same-length changed output bytes cannot become a registered Artifact"
    );
    assert!(
        !directory.path().join("sealed-stdout.log").exists(),
        "a refused original output must not create a purportedly immutable receipt"
    );
}

#[test]
fn original_completed_process_wins_a_later_stop_intent_without_false_cancellation() {
    let directory = tempfile::tempdir().unwrap();
    let mut attempt = admitted_windows_attempt(directory.path());
    attempt.state = AttemptState::Stopping;
    attempt.termination_intent = AttemptTerminationIntent::StopRequested;
    let stdout = b"completed-before-stop-effect\n";
    fs::write(directory.path().join("stdout.log"), stdout).unwrap();
    fs::write(directory.path().join("stderr.log"), b"").unwrap();
    fs::write(
        directory.path().join("result.json"),
        serde_json::to_vec(&native_launcher_result(&attempt, stdout)).unwrap(),
    )
    .unwrap();
    let terminal = prepare_runner_terminal_from_bundle(&attempt).unwrap();
    assert_eq!(terminal.state, AttemptState::Succeeded);
    assert_eq!(
        terminal.reason_code,
        "PROCESS_COMPLETED_BEFORE_STOP_EFFECTIVE"
    );
    assert_eq!(terminal.artifacts[0].digest, sha256_bytes(stdout));
}
