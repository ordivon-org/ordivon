use super::super::{RuntimeError, RuntimeErrorCode};

pub(super) fn map_universal_error(error: crate::UniversalExecError) -> RuntimeError {
    RuntimeError::new(
        RuntimeErrorCode::InvalidRequest,
        error.message,
        error.field.as_deref(),
        error.retryable,
    )
}
