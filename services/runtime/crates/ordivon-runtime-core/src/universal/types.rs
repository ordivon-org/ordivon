//! Original Universal Runtime wire contracts, decomposed by independently observable capability.
//! All original type names, serialization, shape validation and consumer imports remain stable.
use super::{
    invalid, parse_sha256_digest, validate_id, validate_relative_path, UniversalExecError,
    MAX_WORKSPACE_IO_BYTES, UNIVERSAL_EXEC_SCHEMA_VERSION, WORKSPACE_ID_MAX_LENGTH,
    WORKSPACE_ID_MIN_LENGTH, WORKSPACE_ID_PATTERN,
};

mod workspace_identity;
pub use workspace_identity::GitWorkspaceCreateRequest;

mod workspace_lifecycle;
pub(crate) use workspace_lifecycle::WorkspaceRecord;
pub use workspace_lifecycle::{
    CompactWorkspaceOpenResult, WorkspaceCloseRequest, WorkspaceCloseResult,
    WorkspaceClosureDisposition,
};

mod workspace_content;
pub use workspace_content::{
    CompactWorkspaceReadResult, CompactWorkspaceSliceResult, WorkspaceContentMetadata,
    WorkspaceContentReadResult, WorkspaceContentRequest, WorkspaceFileMetadata,
    WorkspaceFileReadResult, WorkspaceFileRequest, WorkspaceReadRequest, WorkspaceReadSliceRequest,
};
pub(crate) use workspace_content::{
    WorkspaceReadResult, WorkspaceReadSliceResult, WorkspaceWriteRequest, WorkspaceWriteResult,
};

mod workspace_change;
pub(crate) use workspace_change::WorkspaceDiffResult;
pub use workspace_change::{
    CompactWorkspaceDiffResult, WorkspaceChangeCursor, WorkspaceChangeEntry, WorkspaceChangeKind,
    WorkspaceChangePageRequest, WorkspaceChangePageResult, WorkspaceDiffRequest,
    WorkspaceRenamedPath, MAX_WORKSPACE_CHANGE_PAGE_ENTRIES,
};

mod workspace_mutation;
pub use workspace_mutation::{
    WorkspaceMutateRequest, WorkspaceMutateResult, WorkspaceMutation, WorkspaceMutationMode,
    WorkspaceMutationResult,
};

mod runner_protocol;
pub(crate) use runner_protocol::{
    CapturedOutput, RunnerExecutionStep, RunnerHostDependencyCommitment, RunnerInputCommitment,
    RunnerPayloadConfig, RunnerProgress, RunnerRequest, RunnerResult, RunnerStartEvidence,
    RunnerStepResult, RunnerTerminalStatus,
};

fn is_false(value: &bool) -> bool {
    !*value
}

fn default_schema_version() -> u32 {
    UNIVERSAL_EXEC_SCHEMA_VERSION
}

fn require_schema(version: u32) -> Result<(), UniversalExecError> {
    if version != UNIVERSAL_EXEC_SCHEMA_VERSION {
        return Err(invalid(
            "unsupported universal executor schema version",
            "schemaVersion",
        ));
    }
    Ok(())
}

fn valid_digest(value: &str) -> bool {
    parse_sha256_digest(value).is_some()
}
