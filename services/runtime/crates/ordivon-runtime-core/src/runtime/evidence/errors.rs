use super::super::{RuntimeError, RuntimeErrorCode};

pub(super) fn map_universal_error(error: crate::UniversalExecError) -> RuntimeError {
    RuntimeError::new(
        RuntimeErrorCode::InvalidRequest,
        error.message,
        error.field.as_deref(),
        error.retryable,
    )
}

pub(super) use super::super::error::nonretryable_io_error as io_error;
