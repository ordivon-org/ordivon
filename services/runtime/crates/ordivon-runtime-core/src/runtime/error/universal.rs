//! Storage-neutral executor error projection shared by PG and legacy Runtime.
use super::*;

pub(crate) fn map_universal_error(error: crate::UniversalExecError) -> RuntimeError {
    use crate::UniversalExecErrorCode as UniversalCode;

    let code = match error.code {
        UniversalCode::InvalidRequest => RuntimeErrorCode::InvalidRequest,
        UniversalCode::WorkspaceExists => RuntimeErrorCode::WorkspaceExists,
        UniversalCode::WorkspaceNotFound => RuntimeErrorCode::WorkspaceNotFound,
        UniversalCode::WorkspacePathNotFound => RuntimeErrorCode::WorkspacePathNotFound,
        UniversalCode::WorkspaceDirty => RuntimeErrorCode::WorkspaceDirty,
        UniversalCode::WorkspacePathDenied => RuntimeErrorCode::WorkspacePathDenied,
        UniversalCode::RevisionNotFound => RuntimeErrorCode::RevisionNotFound,
        UniversalCode::RevisionMismatch => RuntimeErrorCode::RevisionMismatch,
        UniversalCode::WorkspaceStateMismatch
        | UniversalCode::InputStateMismatch
        | UniversalCode::HostDependencyRuntimeDrift
        | UniversalCode::ExecutableRuntimeDrift => RuntimeErrorCode::WorkspaceStateMismatch,
        UniversalCode::WorkspaceMutationIncomplete => RuntimeErrorCode::ReconciliationRequired,
        UniversalCode::ArtifactNotFound => RuntimeErrorCode::ArtifactNotFound,
        UniversalCode::ArtifactNotUtf8 => RuntimeErrorCode::ArtifactNotUtf8,
        UniversalCode::OutputLimitExceeded => RuntimeErrorCode::OutputLimitExceeded,
        UniversalCode::ToolUnavailable => RuntimeErrorCode::ToolUnavailable,
        UniversalCode::ToolFailed => RuntimeErrorCode::ToolFailed,
        UniversalCode::IoError => RuntimeErrorCode::IoError,
        UniversalCode::WorkspaceCapacityExceeded => RuntimeErrorCode::WorkspaceCapacityExceeded,
        UniversalCode::MetadataCorrupt => RuntimeErrorCode::MetadataCorrupt,
    };
    RuntimeError::new(code, error.message, error.field.as_deref(), error.retryable)
}
