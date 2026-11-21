//! Read-only observation request bounds, independent of execution admission.
use super::super::{
    JobObserveRequest, RuntimeError, RuntimeResult, MAX_TASK_TAIL_BYTES, MAX_TASK_WAIT_MS,
    RUNTIME_SCHEMA_VERSION,
};

pub(in crate::runtime) fn validate_observe_request(
    request: &JobObserveRequest,
) -> RuntimeResult<()> {
    if request.schema_version != RUNTIME_SCHEMA_VERSION {
        return Err(RuntimeError::invalid(
            "unsupported runtime schema version",
            "schemaVersion",
        ));
    }
    if request.wait_ms > MAX_TASK_WAIT_MS
        || request.stdout_tail_bytes > MAX_TASK_TAIL_BYTES
        || request.stderr_tail_bytes > MAX_TASK_TAIL_BYTES
    {
        return Err(RuntimeError::invalid(
            "observe bounds exceed runtime limits",
            "waitMs",
        ));
    }
    Ok(())
}
