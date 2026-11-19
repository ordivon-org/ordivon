use serde::Deserialize;
use std::fs;
use std::path::Path;

use super::{
    ArtifactRegistration, AttemptRecord, AttemptState, AttemptTerminationIntent, RuntimeError,
    RuntimeErrorCode, RuntimeResult, TerminalCommit,
};
use crate::universal::{
    sha256_bytes, sha256_file, CapturedOutput, RunnerRequest, RunnerResourceReceipt, RunnerResult,
    RunnerTerminalStatus, RESOURCE_RECEIPT_FILE, RESOURCE_RECEIPT_PROVIDER_LINUX_CGROUP_V2,
    RESOURCE_RECEIPT_SCHEMA_VERSION, RESOURCE_RECEIPT_SCOPE_ATTEMPT_CGROUP,
    UNIVERSAL_EXEC_SCHEMA_VERSION,
};

pub(crate) const RESULT_FILE: &str = "result.json";
const REQUEST_FILE: &str = "request.json";
const STDOUT_FILE: &str = "stdout.log";
const STDERR_FILE: &str = "stderr.log";
const WORKSPACE_SOURCE_OBSERVATION_FILE: &str = "workspace-source-observation.json";

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct WorkspaceSourceObservationEvidence {
    schema_version: u32,
    task_id: String,
    job_id: String,
    attempt_id: String,
    launch_token_digest: String,
    committed_workspace_source_digest: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    observed_workspace_source_digest: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    matches_commitment: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    observation_error_code: Option<String>,
    observed_unix_ms: u128,
}

pub(crate) fn prepare_runner_terminal_from_bundle(
    current: &AttemptRecord,
) -> RuntimeResult<TerminalCommit> {
    let result_path = Path::new(&current.bundle_path).join(RESULT_FILE);
    let bytes = fs::read(&result_path).map_err(|error| io_error("read Runner result", error))?;
    let result: RunnerResult = serde_json::from_slice(&bytes).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            format!("invalid Runner result: {error}"),
            Some("result"),
            false,
        )
    })?;
    if result.task_id != current.attempt_id
        || result.job_id.as_deref() != Some(current.job_id.as_str())
        || result.attempt_id.as_deref() != Some(current.attempt_id.as_str())
        || result.launch_token_digest.as_deref() != Some(current.launch_token_digest.as_str())
        || result.payload_uid.is_some()
        || result.payload_gid.is_some()
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ResultIdentityConflict,
            "Runner result identity does not match committed Attempt",
            Some("result"),
            false,
        ));
    }
    let result_digest = sha256_bytes(&bytes);
    let stdout = validate_captured_output(current, &result.stdout, true)?;
    let stderr = validate_captured_output(current, &result.stderr, false)?;
    let (state, reason_code) = match result.status {
        RunnerTerminalStatus::Completed
            if current.state == AttemptState::Stopping
                || current.termination_intent == AttemptTerminationIntent::StopRequested =>
        {
            (
                AttemptState::Succeeded,
                "PROCESS_COMPLETED_BEFORE_STOP_EFFECTIVE",
            )
        }
        RunnerTerminalStatus::Completed => (AttemptState::Succeeded, "PROCESS_EXIT_ZERO"),
        RunnerTerminalStatus::Failed if result.timed_out => {
            (AttemptState::TimedOut, "DEADLINE_EXCEEDED")
        }
        RunnerTerminalStatus::Failed
            if result.infrastructure_error_code.as_deref() == Some("WORKSPACE_STATE_MISMATCH") =>
        {
            (AttemptState::Failed, "WORKSPACE_SOURCE_PRECONDITION_DRIFT")
        }
        RunnerTerminalStatus::Failed
            if result.infrastructure_error_code.as_deref() == Some("INPUT_STATE_MISMATCH") =>
        {
            (AttemptState::Failed, "INPUT_PRECONDITION_DRIFT")
        }
        RunnerTerminalStatus::Failed
            if result.infrastructure_error_code.as_deref()
                == Some("HOST_DEPENDENCY_RUNTIME_DRIFT") =>
        {
            (AttemptState::Failed, "HOST_DEPENDENCY_RUNTIME_DRIFT")
        }
        RunnerTerminalStatus::Failed
            if result.infrastructure_error_code.as_deref() == Some("EXECUTABLE_RUNTIME_DRIFT") =>
        {
            (AttemptState::Failed, "EXECUTABLE_RUNTIME_DRIFT")
        }
        RunnerTerminalStatus::Failed if result.infrastructure_error_code.is_some() => {
            (AttemptState::Failed, "RUNNER_INFRASTRUCTURE_FAILURE")
        }
        RunnerTerminalStatus::Failed => (AttemptState::Failed, "PROCESS_EXIT_NONZERO"),
        RunnerTerminalStatus::Cancelled => (AttemptState::Cancelled, "STOP_REQUESTED"),
    };
    let infrastructure_error_digest = result
        .infrastructure_error
        .as_deref()
        .map(|message| sha256_bytes(message.as_bytes()));
    let mut artifacts = vec![stdout, stderr];
    artifacts.push(ArtifactRegistration {
        artifact_id: format!("{}.result", current.attempt_id),
        kind: "execution_result".to_string(),
        relative_path: RESULT_FILE.to_string(),
        digest: result_digest.clone(),
        media_type: "application/json".to_string(),
        byte_length: u64::try_from(bytes.len()).unwrap_or(u64::MAX),
        truncated: false,
    });
    if let Some(receipt) = validate_resource_receipt(current)? {
        artifacts.push(receipt);
    }
    Ok(TerminalCommit {
        attempt_id: current.attempt_id.clone(),
        expected_row_version: current.row_version,
        state,
        result_digest,
        exit_code: result.exit_code,
        infrastructure_error_digest,
        finished_at_ms: u64::try_from(result.finished_unix_ms).unwrap_or(u64::MAX),
        artifacts,
        reason_code: reason_code.to_string(),
    })
}

/// Terminal-state-indexed source observation obligation. These states are
/// mutually exclusive; a pair of booleans admitted contradictory requests.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum SourceObservationRequirement {
    Unconstrained,
    MustMatch,
    MustDiffer,
}

impl SourceObservationRequirement {
    pub(crate) fn for_terminal(state: AttemptState, reason: &str) -> Self {
        if state == AttemptState::Succeeded {
            Self::MustMatch
        } else if reason == "WORKSPACE_SOURCE_PRECONDITION_DRIFT" {
            Self::MustDiffer
        } else {
            Self::Unconstrained
        }
    }
}

fn validate_source_observation_relation(
    observed: Option<&str>,
    matches: Option<bool>,
    observation_error: Option<&str>,
    committed: &str,
    requirement: SourceObservationRequirement,
) -> RuntimeResult<()> {
    let valid_digest = |value: &str| {
        value
            .strip_prefix("sha256:")
            .is_some_and(|hex| hex.len() == 64 && hex.bytes().all(|byte| byte.is_ascii_hexdigit()))
    };
    match (observed, matches, observation_error) {
        (Some(observed), Some(matches), None)
            if valid_digest(observed) && matches == (observed == committed) =>
        {
            if requirement == SourceObservationRequirement::MustDiffer && matches {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ArtifactIdentityConflict,
                    "Workspace source drift result carried a matching source observation",
                    Some("workspaceSourceObservation"),
                    false,
                ));
            }
            if requirement == SourceObservationRequirement::MustMatch && !matches {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ArtifactIdentityConflict,
                    "Successful process carried a mismatching Workspace source observation",
                    Some("workspaceSourceObservation"),
                    false,
                ));
            }
        }
        (None, None, Some(error_code))
            if !error_code.is_empty()
                && requirement == SourceObservationRequirement::Unconstrained => {}
        _ => {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Workspace source observation digest/error relation is invalid",
                Some("workspaceSourceObservation"),
                false,
            ));
        }
    }
    Ok(())
}

pub(crate) fn validate_workspace_source_observation_artifact(
    current: &AttemptRecord,
    committed_workspace_source_digest: Option<&str>,
    require_if_committed: bool,
    requirement: SourceObservationRequirement,
) -> RuntimeResult<Option<ArtifactRegistration>> {
    let path = Path::new(&current.bundle_path).join(WORKSPACE_SOURCE_OBSERVATION_FILE);
    if !require_if_committed && !path.exists() {
        return Ok(None);
    }

    let request_path = Path::new(&current.bundle_path).join(REQUEST_FILE);
    let request_bytes =
        fs::read(&request_path).map_err(|error| io_error("read Runner request", error))?;
    let request: RunnerRequest = serde_json::from_slice(&request_bytes).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            format!("invalid Runner request while validating source observation: {error}"),
            Some("workspaceSourceObservation"),
            false,
        )
    })?;
    if request.task_id != current.attempt_id
        || request.job_id.as_deref() != Some(current.job_id.as_str())
        || request.attempt_id.as_deref() != Some(current.attempt_id.as_str())
        || request
            .launch_token
            .as_deref()
            .map(|value| sha256_bytes(value.as_bytes()))
            .as_deref()
            != Some(current.launch_token_digest.as_str())
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ResultIdentityConflict,
            "Runner request identity does not match committed Attempt while validating source observation",
            Some("workspaceSourceObservation"),
            false,
        ));
    }

    if request.workspace_source_digest.as_deref() != committed_workspace_source_digest {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ArtifactIdentityConflict,
            "Runner request Workspace source commitment does not match the Registry execution plan",
            Some("workspaceSourceObservation"),
            false,
        ));
    }

    let committed = committed_workspace_source_digest;
    if committed.is_none() {
        if path.exists() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Workspace source observation exists without a committed source digest",
                Some("workspaceSourceObservation"),
                false,
            ));
        }
        return Ok(None);
    }
    let bytes = match fs::read(&path) {
        Ok(bytes) => bytes,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound && !require_if_committed => {
            return Ok(None);
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Committed Workspace source result omitted exact source observation evidence",
                Some("workspaceSourceObservation"),
                false,
            ));
        }
        Err(error) => return Err(io_error("read Workspace source observation", error)),
    };
    let evidence: WorkspaceSourceObservationEvidence =
        serde_json::from_slice(&bytes).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                format!("invalid Workspace source observation: {error}"),
                Some("workspaceSourceObservation"),
                false,
            )
        })?;
    let committed = committed.expect("checked above");
    let valid_digest = |value: &str| {
        value
            .strip_prefix("sha256:")
            .is_some_and(|hex| hex.len() == 64 && hex.bytes().all(|byte| byte.is_ascii_hexdigit()))
    };
    if evidence.schema_version != UNIVERSAL_EXEC_SCHEMA_VERSION
        || evidence.task_id != current.attempt_id
        || evidence.job_id != current.job_id
        || evidence.attempt_id != current.attempt_id
        || evidence.launch_token_digest != current.launch_token_digest
        || evidence.committed_workspace_source_digest != committed
        || !valid_digest(&evidence.committed_workspace_source_digest)
        || evidence.observed_unix_ms == 0
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ArtifactIdentityConflict,
            "Workspace source observation identity does not match committed Attempt",
            Some("workspaceSourceObservation"),
            false,
        ));
    }
    validate_source_observation_relation(
        evidence.observed_workspace_source_digest.as_deref(),
        evidence.matches_commitment,
        evidence.observation_error_code.as_deref(),
        committed,
        requirement,
    )?;
    Ok(Some(ArtifactRegistration {
        artifact_id: format!("{}.workspace-source-observation", current.attempt_id),
        kind: "workspace_source_observation".to_string(),
        relative_path: WORKSPACE_SOURCE_OBSERVATION_FILE.to_string(),
        digest: sha256_bytes(&bytes),
        media_type: "application/json".to_string(),
        byte_length: u64::try_from(bytes.len()).unwrap_or(u64::MAX),
        truncated: false,
    }))
}

fn validate_resource_receipt(
    current: &AttemptRecord,
) -> RuntimeResult<Option<ArtifactRegistration>> {
    let path = Path::new(&current.bundle_path).join(RESOURCE_RECEIPT_FILE);
    let bytes = match fs::read(&path) {
        Ok(bytes) => bytes,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(error) => return Err(io_error("read Runner resource receipt", error)),
    };
    let receipt: RunnerResourceReceipt = serde_json::from_slice(&bytes).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::ResultIdentityConflict,
            format!("invalid Runner resource receipt: {error}"),
            Some("resourceReceipt"),
            false,
        )
    })?;
    if receipt.schema_version != RESOURCE_RECEIPT_SCHEMA_VERSION
        || receipt.task_id != current.attempt_id
        || receipt.job_id != current.job_id
        || receipt.attempt_id != current.attempt_id
        || receipt.launch_token_digest != current.launch_token_digest
        || receipt.scope != RESOURCE_RECEIPT_SCOPE_ATTEMPT_CGROUP
        || receipt.provider != RESOURCE_RECEIPT_PROVIDER_LINUX_CGROUP_V2
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ResultIdentityConflict,
            "Runner resource receipt identity does not match committed Attempt",
            Some("resourceReceipt"),
            false,
        ));
    }
    Ok(Some(ArtifactRegistration {
        artifact_id: format!("{}.resource-receipt", current.attempt_id),
        kind: "resource_receipt".to_string(),
        relative_path: RESOURCE_RECEIPT_FILE.to_string(),
        digest: sha256_bytes(&bytes),
        media_type: "application/json".to_string(),
        byte_length: u64::try_from(bytes.len()).unwrap_or(u64::MAX),
        truncated: false,
    }))
}

fn validate_captured_output(
    attempt: &AttemptRecord,
    output: &CapturedOutput,
    stdout: bool,
) -> RuntimeResult<ArtifactRegistration> {
    let expected_file = if stdout { STDOUT_FILE } else { STDERR_FILE };
    let expected_kind = if stdout { "stdout" } else { "stderr" };
    let expected_id = format!("{}.{}", attempt.attempt_id, expected_kind);
    if output.file_name != expected_file || output.artifact_id != expected_id {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ArtifactIdentityConflict,
            "Runner output identity does not match Attempt",
            Some("artifact"),
            false,
        ));
    }
    let path = Path::new(&attempt.bundle_path).join(expected_file);
    let metadata = fs::metadata(&path).map_err(|error| io_error("inspect output", error))?;
    let digest = sha256_file(&path).map_err(map_universal_error)?;
    if digest != output.digest || metadata.len() != output.retained_bytes {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ArtifactIdentityConflict,
            "Runner output digest or byte length changed",
            Some("artifact"),
            false,
        ));
    }
    Ok(ArtifactRegistration {
        artifact_id: expected_id,
        kind: expected_kind.to_string(),
        relative_path: expected_file.to_string(),
        digest,
        media_type: "text/plain; charset=utf-8".to_string(),
        byte_length: metadata.len(),
        truncated: output.truncated,
    })
}

fn map_universal_error(error: crate::UniversalExecError) -> RuntimeError {
    RuntimeError::new(
        RuntimeErrorCode::InvalidRequest,
        error.message,
        error.field.as_deref(),
        error.retryable,
    )
}

fn io_error(context: &str, error: std::io::Error) -> RuntimeError {
    RuntimeError::new(
        RuntimeErrorCode::IoError,
        format!("{context}: {error}"),
        None,
        false,
    )
}

#[cfg(test)]
mod source_observation_semantic_tests {
    use super::{validate_source_observation_relation, SourceObservationRequirement};
    use crate::runtime::AttemptState;

    const COMMITTED: &str =
        "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    const DIFFERENT: &str =
        "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

    #[test]
    fn successful_state_requires_match_even_with_new_terminal_reason() {
        assert_eq!(
            SourceObservationRequirement::for_terminal(
                AttemptState::Succeeded,
                "FUTURE_SUCCESS_REASON"
            ),
            SourceObservationRequirement::MustMatch
        );
        assert_eq!(
            SourceObservationRequirement::for_terminal(
                AttemptState::Succeeded,
                "PROCESS_COMPLETED_BEFORE_STOP_EFFECTIVE"
            ),
            SourceObservationRequirement::MustMatch
        );
        assert_eq!(
            SourceObservationRequirement::for_terminal(
                AttemptState::Failed,
                "WORKSPACE_SOURCE_PRECONDITION_DRIFT"
            ),
            SourceObservationRequirement::MustDiffer
        );
        assert_eq!(
            SourceObservationRequirement::for_terminal(AttemptState::TimedOut, "DEADLINE_EXCEEDED"),
            SourceObservationRequirement::Unconstrained
        );
    }

    #[test]
    fn successful_process_must_not_carry_drifted_source_observation() {
        assert!(
            validate_source_observation_relation(
                Some(DIFFERENT),
                Some(false),
                None,
                COMMITTED,
                SourceObservationRequirement::MustMatch,
            )
            .is_err(),
            "a successful execution must not preserve a source-drift observation"
        );
    }

    #[test]
    fn successful_process_must_not_carry_unresolved_source_observation() {
        assert!(
            validate_source_observation_relation(
                None,
                None,
                Some("UNKNOWN_SOURCE_OBSERVATION"),
                COMMITTED,
                SourceObservationRequirement::MustMatch,
            )
            .is_err(),
            "missing source observation cannot attest a successful process"
        );
    }

    #[test]
    fn successful_process_accepts_committed_source_observation() {
        assert!(validate_source_observation_relation(
            Some(COMMITTED),
            Some(true),
            None,
            COMMITTED,
            SourceObservationRequirement::MustMatch,
        )
        .is_ok());
    }

    #[test]
    fn source_precondition_drift_still_requires_a_real_mismatch() {
        assert!(validate_source_observation_relation(
            Some(DIFFERENT),
            Some(false),
            None,
            COMMITTED,
            SourceObservationRequirement::MustDiffer,
        )
        .is_ok());
        assert!(validate_source_observation_relation(
            Some(COMMITTED),
            Some(true),
            None,
            COMMITTED,
            SourceObservationRequirement::MustDiffer,
        )
        .is_err());
    }
}

#[cfg(test)]
mod windows_native_result_to_pg_terminal_contract_tests {
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
        assert_eq!(terminal.artifacts[2].kind, "execution_result");
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
}
