use super::super::super::{AttemptRecord, RuntimeError, RuntimeErrorCode, RuntimeResult};
use super::super::errors::io_error;
use super::super::{REQUEST_FILE, RESULT_FILE};
use crate::universal::{sha256_bytes, RunnerRequest, RunnerResult};
use std::{fs, path::Path};

pub(super) fn read_and_validate_runner_result(
    current: &AttemptRecord,
) -> RuntimeResult<(RunnerResult, String, usize)> {
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
    // Payload identity comes from the original committed Runner request, not
    // from the result (which may omit or falsify UID/GID). Where a legacy
    // fixture has no committed request, it must still have NO payload.
    let mut committed_payload = None;
    let request_path = Path::new(&current.bundle_path).join(REQUEST_FILE);
    if let Some(committed) = current
        .bundle_digest
        .as_deref()
        .filter(|_| request_path.is_file())
    {
        let request_bytes = fs::read(&request_path)
            .map_err(|err| io_error("read committed Runner request", err))?;
        if sha256_bytes(&request_bytes) != committed {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ResultIdentityConflict,
                "Runner request bytes disagree with committed PG bundle digest",
                Some("result"),
                false,
            ));
        }
        let request: RunnerRequest = serde_json::from_slice(&request_bytes).map_err(|err| {
            RuntimeError::new(
                RuntimeErrorCode::ResultIdentityConflict,
                format!("invalid committed Runner request: {err}"),
                Some("result"),
                false,
            )
        })?;
        if request.job_id.as_deref() != Some(current.job_id.as_str())
            || request.attempt_id.as_deref() != Some(current.attempt_id.as_str())
            || request.task_id != current.attempt_id
            || request
                .launch_token
                .as_deref()
                .map(|token| sha256_bytes(token.as_bytes()))
                .as_deref()
                != Some(current.launch_token_digest.as_str())
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ResultIdentityConflict,
                "payload-bearing Runner request is not the original Attempt",
                Some("result"),
                false,
            ));
        }
        committed_payload = request.payload.map(|p| (p.uid, p.gid));
    } else if result.payload_uid.is_some() || result.payload_gid.is_some() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ResultIdentityConflict,
            "payload result has no committed Runner request identity",
            Some("result"),
            false,
        ));
    }
    if result.task_id != current.attempt_id
        || result.job_id.as_deref() != Some(current.job_id.as_str())
        || result.attempt_id.as_deref() != Some(current.attempt_id.as_str())
        || result.launch_token_digest.as_deref() != Some(current.launch_token_digest.as_str())
        || result.payload_uid != committed_payload.map(|p| p.0)
        || result.payload_gid != committed_payload.map(|p| p.1)
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ResultIdentityConflict,
            "Runner result identity does not match committed Attempt",
            Some("result"),
            false,
        ));
    }
    let result_digest = sha256_bytes(&bytes);
    Ok((result, result_digest, bytes.len()))
}
