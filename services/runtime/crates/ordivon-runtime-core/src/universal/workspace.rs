use std::collections::{BTreeMap, BTreeSet, BinaryHeap};
use std::fs::{self, File};
use std::io::{BufRead, BufReader, Read};
#[cfg(unix)]
use std::os::unix::ffi::OsStrExt;
#[cfg(unix)]
use std::os::unix::fs::{MetadataExt, PermissionsExt};
#[cfg(windows)]
use std::os::windows::ffi::OsStrExt as WindowsOsStrExt;
#[cfg(windows)]
use std::os::windows::fs::MetadataExt as WindowsMetadataExt;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::thread::{self, JoinHandle};

use super::{
    canonical_directory, invalid, io_error, now_unix_ms, open_directory_nofollow,
    open_regular_file_beneath, sha256_bytes, sha256_file, validate_relative_path,
    write_bytes_atomic, write_json_atomic, GitWorkspaceCreateRequest, UniversalExecError,
    UniversalExecErrorCode, UniversalExecutorConfig, WorkspaceChangeCursor, WorkspaceChangeEntry,
    WorkspaceChangeKind, WorkspaceChangePageRequest, WorkspaceChangePageResult,
    WorkspaceCloseRequest, WorkspaceCloseResult, WorkspaceClosureDisposition,
    WorkspaceContentMetadata, WorkspaceContentReadResult, WorkspaceContentRequest,
    WorkspaceDiffRequest, WorkspaceDiffResult, WorkspaceReadRequest, WorkspaceReadResult,
    WorkspaceRecord, WorkspaceRenamedPath, WorkspaceWriteRequest, WorkspaceWriteResult,
    UNIVERSAL_EXEC_SCHEMA_VERSION,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct ClosedWorkspaceRecord {
    schema_version: u32,
    state: String,
    workspace_id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    source_repo: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    source_revision: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    final_head: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    source_state_digest: Option<String>,
    closed_unix_ms: u128,
    removal_result: String,
}

#[derive(Debug, Default)]
pub(crate) struct WorkspaceChangeProjection {
    pub(crate) changed: Vec<String>,
    pub(crate) modified: Vec<String>,
    pub(crate) added: Vec<String>,
    pub(crate) deleted: Vec<String>,
    pub(crate) renamed: Vec<WorkspaceRenamedPath>,
    pub(crate) untracked: Vec<String>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct WorkspaceSourceState {
    schema_version: u32,
    head_revision: String,
    index_digest: String,
    tracked: Vec<WorkspaceSourceEntry>,
    untracked: Vec<WorkspaceSourceEntry>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct WorkspaceSourceEntry {
    path: String,
    kind: String,
    mode: u32,
    byte_length: u64,
    digest: String,
}

include!("workspace/records.rs");
include!("workspace/file_io.rs");
include!("workspace/changes.rs");
include!("workspace/source_state.rs");
include!("workspace/close_recovery.rs");
include!("workspace/paths_git.rs");

#[cfg(test)]
mod bounded_output_tests {
    use super::*;
    use std::time::{Duration, Instant};

    #[test]
    fn bounded_command_stdout_stops_after_one_byte_beyond_budget() {
        let mut command = Command::new("/usr/bin/python3");
        command.args([
            "-c",
            "import sys; sys.stdout.write('x' * 5000000); sys.stdout.flush()",
        ]);
        let started = Instant::now();
        let (bytes, truncated) =
            bounded_command_stdout(&mut command, 64, &[0], "large test output").unwrap();
        assert!(truncated);
        assert_eq!(bytes.len(), 64);
        assert!(started.elapsed() < Duration::from_secs(2));
    }
}
