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

pub(crate) fn validate_workspace_source_observation_artifact(
    current: &AttemptRecord,
    committed_workspace_source_digest: Option<&str>,
    require_if_committed: bool,
    require_mismatch: bool,
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
    match (
        evidence.observed_workspace_source_digest.as_deref(),
        evidence.matches_commitment,
        evidence.observation_error_code.as_deref(),
    ) {
        (Some(observed), Some(matches), None)
            if valid_digest(observed) && matches == (observed == committed) =>
        {
            if require_mismatch && matches {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::ArtifactIdentityConflict,
                    "Workspace source drift result carried a matching source observation",
                    Some("workspaceSourceObservation"),
                    false,
                ));
            }
        }
        (None, None, Some(error_code)) if !error_code.is_empty() && !require_mismatch => {}
        _ => {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Workspace source observation digest/error relation is invalid",
                Some("workspaceSourceObservation"),
                false,
            ));
        }
    }
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
