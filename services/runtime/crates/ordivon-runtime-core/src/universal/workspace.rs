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
    canonical_directory, ensure_workspace_mutation_quiescent, invalid, io_error, now_unix_ms,
    open_directory_nofollow, open_regular_file_beneath, parse_sha256_digest, sha256_bytes,
    sha256_file, validate_relative_path, write_bytes_atomic, write_json_atomic,
    GitWorkspaceCreateRequest, UniversalExecError, UniversalExecErrorCode, UniversalExecutorConfig,
    WorkspaceChangeCursor, WorkspaceChangeEntry, WorkspaceChangeKind, WorkspaceChangePageRequest,
    WorkspaceChangePageResult, WorkspaceCloseRequest, WorkspaceCloseResult,
    WorkspaceClosureDisposition, WorkspaceContentMetadata, WorkspaceContentReadResult,
    WorkspaceContentRequest, WorkspaceDiffRequest, WorkspaceDiffResult, WorkspaceFileMetadata,
    WorkspaceFileReadResult, WorkspaceFileRequest, WorkspaceReadRequest, WorkspaceReadResult,
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
    #[serde(default, skip_serializing, rename = "workspaceId")]
    legacy_workspace_id: String,
    #[serde(default, skip_serializing, rename = "sourceRepo")]
    _legacy_source_repo: Option<String>,
    #[serde(default, skip_serializing, rename = "sourceRevision")]
    _legacy_source_revision: Option<String>,
    #[serde(default, skip_serializing, rename = "finalHead")]
    _legacy_final_head: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    source_state_digest: Option<String>,
    #[serde(default, skip_serializing, rename = "closedUnixMs")]
    _legacy_closed_unix_ms: Option<u128>,
    #[serde(default, skip_serializing, rename = "removalResult")]
    _legacy_removal_result: Option<String>,
}

// A close-intent lives in the EXISTING native record path. Unlike a PG-only
// transaction, this survives interruption between Git worktree removal and
// writing the final closed tombstone, with the original physical CAS witness.
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct ClosingWorkspaceRecord {
    schema_version: u32,
    state: String,
    record: WorkspaceRecord,
    source_state_digest: String,
    final_head: String,
    force: bool,
    consumer_released: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum WorkspaceHeadMode {
    Detached,
    Branch,
}

impl WorkspaceHeadMode {
    pub(crate) const fn as_str(self) -> &'static str {
        match self {
            Self::Detached => "detached",
            Self::Branch => "branch",
        }
    }
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

// A Git subprocess must use its explicit -C repository, never a foreign
// repository/object store inherited from an Agent's ambient environment.
// Keep PATH/HOME and other non-Git tool settings; no separate Git authority.
fn workspace_git_command() -> Command {
    let mut command = Command::new("git");
    for (key, _) in std::env::vars_os() {
        if key.to_string_lossy().starts_with("GIT_") {
            command.env_remove(key);
        }
    }
    command
}

include!("workspace/records.rs");
include!("workspace/file_io.rs");
include!("workspace/changes.rs");
include!("workspace/source_state.rs");
// Explicit Rust module interfaces: no include! flattening for OS consumers
// or private-Git output qualification. Existing Workspace close orchestration
// invokes exactly these two capabilities, without importing their internals.
#[cfg(target_os = "linux")]
mod systemd_consumers;
#[cfg(target_os = "linux")]
use systemd_consumers::ensure_no_closing_workspace_systemd_consumer;
mod git_recovery;
use git_recovery::{
    ensure_rescue_ref, recover_missing_workspace_head, registered_workspace_head,
    remove_git_worktree_from_workspace, remove_registered_workspace_with_broken_metadata,
    remove_residual_workspace_directory,
};
mod private_git_outputs;
// Shared OPENING metadata error vocabulary for record and Git capabilities.
fn unfinished_open_error(reason: &str) -> UniversalExecError {
    UniversalExecError::new(
        UniversalExecErrorCode::MetadataCorrupt,
        format!("Workspace opening cannot be reconciled safely: {reason}"),
        Some("workspaceId"),
        false,
    )
}

use private_git_outputs::workspace_private_git_has_outputs;
include!("workspace/close_recovery.rs");
include!("workspace/paths_git.rs");

#[cfg(test)]
mod bounded_output_tests {
    use super::*;
    use std::time::{Duration, Instant};

    #[cfg(target_os = "linux")]
    #[test]
    fn workspace_owner_git_env_isolation() {
        fn clean_git(repo: &Path, args: &[&str]) -> String {
            let output = Command::new("/usr/bin/git")
                .env_clear()
                .arg("-C")
                .arg(repo)
                .args(args)
                .output()
                .unwrap();
            assert!(
                output.status.success(),
                "{}",
                String::from_utf8_lossy(&output.stderr)
            );
            String::from_utf8(output.stdout).unwrap().trim().to_string()
        }

        fn init_clean_repo(repo: &Path) -> String {
            fs::create_dir_all(repo).unwrap();
            clean_git(repo, &["init", "-q"]);
            clean_git(repo, &["config", "user.name", "Git Boundary Test"]);
            clean_git(
                repo,
                &["config", "user.email", "git-boundary@example.invalid"],
            );
            fs::write(repo.join("marker"), repo.to_string_lossy().as_bytes()).unwrap();
            clean_git(repo, &["add", "marker"]);
            clean_git(repo, &["commit", "-qm", "owner Git commit"]);
            clean_git(repo, &["rev-parse", "HEAD"])
        }

        if std::env::var_os("ORDIVON_GIT_TEST_CHILD").is_none() {
            let temp = tempfile::tempdir().unwrap();
            let foreign = temp.path().join("foreign");
            init_clean_repo(&foreign);
            let test_name =
                "universal::workspace::bounded_output_tests::workspace_owner_git_env_isolation";
            let executable = std::env::current_exe().unwrap();
            for (key, value) in [
                ("GIT_DIR", foreign.join(".git")),
                ("GIT_OBJECT_DIRECTORY", foreign.join(".git/objects")),
            ] {
                let output = Command::new(&executable)
                    .args(["--exact", test_name, "--nocapture"])
                    .env("ORDIVON_GIT_TEST_CHILD", "1")
                    .env(key, value)
                    .output()
                    .unwrap();
                assert!(
                    output.status.success()
                        && String::from_utf8_lossy(&output.stdout).contains("1 passed"),
                    "{key}: stdout={} stderr={}",
                    String::from_utf8_lossy(&output.stdout),
                    String::from_utf8_lossy(&output.stderr)
                );
            }
            return;
        }

        let temp = tempfile::tempdir().unwrap();
        let owner = temp.path().join("owner");
        let owner_head = init_clean_repo(&owner);
        // Every Owner-native Git query must follow -C owner rather than the
        // unrelated environment-level Git repository/object store.
        assert_eq!(resolve_git_commit(&owner, &owner_head).unwrap(), owner_head);
        let (status_head, _, dirty) = workspace_head_and_dirty_at(&owner).unwrap();
        assert_eq!(status_head, owner_head);
        assert!(!dirty);
        assert_eq!(
            git_output(&owner, ["rev-parse", "HEAD"]).unwrap().trim(),
            owner_head
        );
    }

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
