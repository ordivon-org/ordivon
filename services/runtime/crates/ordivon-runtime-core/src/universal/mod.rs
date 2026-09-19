mod config;
mod error;
mod fsutil;
mod mutation;
mod projection;
#[cfg(unix)]
mod runner;
mod types;
mod workspace;

pub use config::{UniversalExecutorConfig, MAX_WORKSPACE_IO_BYTES, UNIVERSAL_EXEC_SCHEMA_VERSION};
pub use error::{UniversalExecError, UniversalExecErrorCode};
pub use fsutil::{
    ENVIRONMENT_VARIABLE_NAME_PATTERN, WORKSPACE_ID_MAX_LENGTH, WORKSPACE_ID_MIN_LENGTH,
    WORKSPACE_ID_PATTERN,
};
pub use mutation::mutate_workspace;
pub(crate) use mutation::read_workspace_slice;
pub(crate) use projection::create_git_workspace;
pub use projection::{
    read_workspace_slice_compact, read_workspace_text_compact, workspace_diff_compact,
};
#[cfg(unix)]
pub use runner::run_job_runner;
pub use types::{
    CompactWorkspaceDiffResult, CompactWorkspaceOpenResult, CompactWorkspaceReadResult,
    CompactWorkspaceSliceResult, GitWorkspaceCreateRequest, WorkspaceChangeCursor,
    WorkspaceChangeEntry, WorkspaceChangeKind, WorkspaceChangePageRequest,
    WorkspaceChangePageResult, WorkspaceCloseRequest, WorkspaceCloseResult,
    WorkspaceClosureDisposition, WorkspaceContentMetadata, WorkspaceContentReadResult,
    WorkspaceContentRequest, WorkspaceDiffRequest, WorkspaceMutateRequest, WorkspaceMutateResult,
    WorkspaceMutation, WorkspaceMutationMode, WorkspaceMutationResult, WorkspaceReadRequest,
    WorkspaceReadSliceRequest, WorkspaceRenamedPath, WorkspaceWriteRequest, WorkspaceWriteResult,
    MAX_WORKSPACE_CHANGE_PAGE_ENTRIES,
};
pub(crate) use types::{
    WorkspaceDiffResult, WorkspaceReadResult, WorkspaceReadSliceResult, WorkspaceRecord,
};
pub(crate) use workspace::{
    create_git_workspace_record, load_workspace_record, read_workspace_text, workspace_diff,
};
pub use workspace::{read_workspace_content, workspace_changes_page};
pub(crate) use workspace::{remove_git_workspace, write_workspace_text};
#[cfg(any(feature = "transactional-runtime", test))]
pub use workspace::{workspace_head_revision, workspace_source_state_digest};

pub(crate) use config::canonical_directory;
pub(crate) use fsutil::{
    invalid, io_error, now_unix_ms, open_directory_nofollow, open_regular_file_beneath,
    rename_path_durable, sha256_bytes, sha256_file, sync_directory, validate_env,
    validate_exec_payload, validate_id, validate_relative_path, write_bytes_atomic,
    write_json_atomic,
};
#[cfg(test)]
pub(crate) use fsutil::{
    linux_exec_payload_limit_bytes, linux_exec_string_limit_bytes, validate_args,
};
#[cfg(unix)]
pub(crate) use types::RunnerStepResult;
pub(crate) use types::{
    CapturedOutput, RunnerExecutionStep, RunnerHostDependencyCommitment, RunnerInputCommitment,
    RunnerPayloadConfig, RunnerProgress, RunnerRequest, RunnerResult, RunnerStartEvidence,
    RunnerTerminalStatus,
};
#[cfg(feature = "transactional-runtime")]
pub(crate) use workspace::resolve_workspace_cwd;
#[cfg(unix)]
pub(crate) use workspace::workspace_source_state_digest_at;
pub(crate) use workspace::{
    list_open_workspace_record_inventory, preflight_workspace_write_path, remove_workspace_file,
    resolve_existing_workspace_path, workspace_cleanup_dependents, workspace_git_common_dir_at,
    workspace_head_and_dirty_at,
};
#[cfg(feature = "operator-tools")]
pub(crate) use workspace::{workspace_change_projection_at, workspace_head_revision_at};

#[cfg(test)]
mod tests;
