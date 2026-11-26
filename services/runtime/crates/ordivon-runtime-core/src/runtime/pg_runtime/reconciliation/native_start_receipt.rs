//! Exact native Runner start receipt and its original PG observation.
//! A committed RUNNER_BOUND event must not be replaced by a later file.
use super::{
    io, pg_read_error, universal, AttemptRecord, AttemptState, PgAdmissionStore,
    RunnerStartEvidence, RuntimeError, RuntimeErrorCode, RuntimeResult,
};
use std::io::Read;
use std::path::Path;

fn conflict(a: &AttemptRecord) -> RuntimeError {
    RuntimeError::new(
        RuntimeErrorCode::ResultIdentityConflict,
        "native Runner start evidence disagrees with the original Attempt or committed RUNNER_BOUND",
        Some("runnerStart"),
        false,
    )
    .with_operation_id(&a.job_id)
}

/// Open the private Attempt directory and receipt without following aliases.
/// Missing is not evidence of an unissued or settled native operation.
pub(super) fn read_native_start_receipt(path: &Path) -> RuntimeResult<Option<Vec<u8>>> {
    let name = Path::new("runner-start.json");
    match std::fs::symlink_metadata(path.join(name)) {
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(error) => return Err(io(error)),
        Ok(meta) if !meta.file_type().is_file() => {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ResultIdentityConflict,
                "Runner start evidence is not a regular file",
                Some("runnerStart"),
                false,
            ));
        }
        Ok(_) => {}
    }
    let dir = universal::open_directory_nofollow(path).map_err(io)?;
    let file = universal::open_regular_file_beneath(&dir, name, true).map_err(io)?;
    // A native start receipt is a small fixed-field identity record, not a log.
    const MAX_START_RECEIPT_BYTES: u64 = 64 * 1024;
    let mut bytes = Vec::new();
    file.take(MAX_START_RECEIPT_BYTES + 1)
        .read_to_end(&mut bytes)
        .map_err(io)?;
    if bytes.len() as u64 > MAX_START_RECEIPT_BYTES {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ResultIdentityConflict,
            "Runner start identity exceeds native receipt bounds",
            Some("runnerStart"),
            false,
        ));
    }
    Ok(Some(bytes))
}

/// Bind the exact bytes to the current Attempt and its original PG event.
/// A fast Runner can finish before RUNNER_BOUND; that is distinct from a
/// previously bound Runner whose evidence is now missing or contradictory.
pub(super) fn qualify_native_start_receipt(
    db: &mut PgAdmissionStore,
    a: &AttemptRecord,
    provider: &serde_json::Value,
    bytes: &[u8],
) -> RuntimeResult<(RunnerStartEvidence, String)> {
    let start: RunnerStartEvidence = serde_json::from_slice(bytes).map_err(|_| conflict(a))?;
    let expected_unit = format!("ordivon-pg-{}.service", a.attempt_id);
    let expected_cgroup = format!("/system.slice/{expected_unit}");
    let expected_provider = provider["executionProvider"]["executableDigest"]
        .as_str()
        .filter(|digest| !digest.is_empty())
        .ok_or_else(|| conflict(a))?;
    if start.schema_version != 1
        || start.job_id != a.job_id
        || start.attempt_id != a.attempt_id
        || start.launch_token_digest != a.launch_token_digest
        || a.unit_name != expected_unit
        || start.unit_name != expected_unit
        || start.control_group != expected_cgroup
        || start.invocation_id.is_empty()
        || start.namespace_pid == 0
        || start.namespace_process_start_identity.is_empty()
        || start.observed_unix_ms == 0
        || start.runner_executable_digest.as_deref() != Some(expected_provider)
    {
        return Err(conflict(a));
    }
    let digest = universal::sha256_bytes(bytes);
    // Use the original PG Attempt version/current pointer, not an independent
    // latest-Job lookup. The existing terminal writer still owns the final CAS.
    let rows = db
        .client
        .query(
            "SELECT a.started_at_ms,a.state,e.event_id,e.origin,e.previous_state,e.new_state,
                e.reason_code,e.detail_json,e.detail_digest,e.observed_at_ms
         FROM jobs j JOIN attempts a ON a.attempt_id=j.current_attempt_id AND a.job_id=j.job_id
         LEFT JOIN job_events e ON e.job_id=a.job_id AND e.attempt_id=a.attempt_id
                              AND e.event_type='RUNNER_BOUND'
         WHERE j.job_id=$1 AND a.attempt_id=$2 AND a.row_version=$3 AND j.resolution IS NULL",
            &[&a.job_id, &a.attempt_id, &(a.row_version as i64)],
        )
        .map_err(pg_read_error)?;
    if rows.is_empty() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ReconciliationRequired,
            "current Attempt changed during native start receipt qualification",
            Some("currentAttemptId"),
            true,
        )
        .with_operation_id(&a.job_id));
    }
    if rows.len() != 1 {
        return Err(conflict(a));
    }
    let row = &rows[0];
    if row.get::<_, String>(1) != a.state.as_db() {
        return Err(conflict(a));
    }
    let started: Option<i64> = row.get(0);
    let bound_event: Option<String> = row.get(2);
    if started.is_none() && bound_event.is_none() && a.state != AttemptState::Running {
        return Ok((start, digest));
    }
    let expected_detail = serde_json::json!({
        "runnerStartDigest": digest,
        "invocationId": start.invocation_id,
    })
    .to_string();
    if started.is_none()
        || bound_event.is_none()
        || row.get::<_, Option<String>>(3).as_deref() != Some("SYSTEM_OBSERVED")
        || row.get::<_, Option<String>>(4).as_deref() != Some("starting")
        || row.get::<_, Option<String>>(5).as_deref() != Some("running")
        || row.get::<_, Option<String>>(6).as_deref() != Some("SUPERVISOR_OWNER_MATCHED")
        || row.get::<_, Option<String>>(7).as_deref() != Some(expected_detail.as_str())
        || row.get::<_, Option<String>>(8).as_deref()
            != Some(universal::sha256_bytes(expected_detail.as_bytes()).as_str())
        || row.get::<_, Option<i64>>(9) != started
    {
        return Err(conflict(a));
    }
    Ok((start, digest))
}
