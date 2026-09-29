use std::fs;
use std::path::Path;

use super::{
    ArtifactRegistration, AttemptRecord, AttemptState, AttemptTerminationIntent, RuntimeError,
    RuntimeErrorCode, RuntimeResult, TerminalCommit,
};
use crate::universal::{
    sha256_bytes, sha256_file, CapturedOutput, RunnerResourceReceipt, RunnerResult,
    RunnerTerminalStatus, RESOURCE_RECEIPT_FILE, RESOURCE_RECEIPT_PROVIDER_LINUX_CGROUP_V2,
    RESOURCE_RECEIPT_SCHEMA_VERSION, RESOURCE_RECEIPT_SCOPE_ATTEMPT_CGROUP,
};

pub(crate) const RESULT_FILE: &str = "result.json";
const STDOUT_FILE: &str = "stdout.log";
const STDERR_FILE: &str = "stderr.log";

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
