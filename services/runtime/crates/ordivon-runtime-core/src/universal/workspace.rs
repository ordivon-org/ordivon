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

// Git for Windows does not accept the Win32 extended-length drive prefix
// as a repository/worktree argument. Keep canonical paths in durable identity
// and native filesystem operations; change only the Git subprocess carrier.
fn git_cli_path(path: &Path) -> PathBuf {
    #[cfg(windows)]
    {
        use std::path::{Component, Prefix};
        if matches!(path.components().next(), Some(Component::Prefix(p))
            if matches!(p.kind(), Prefix::VerbatimDisk(_)))
        {
            if let Some(text) = path.to_str().and_then(|s| s.strip_prefix(r"\\?\")) {
                // Verbatim-only filenames are not ordinary Win32 aliases.
                // Leave them unconverted rather than target a different path.
                if path.components().all(|c| match c {
                    Component::Normal(n) => n.to_str().is_some_and(|n| !n.ends_with(['.', ' '])),
                    _ => true,
                }) {
                    return PathBuf::from(text);
                }
            }
        }
    }
    path.to_path_buf()
}

fn git_registered_path_matches(raw: &[u8], expected: &Path) -> bool {
    #[cfg(windows)]
    {
        // Git porcelain uses forward separators and ordinary drive paths.
        // A lexical match is required even for absent worktrees; the caller
        // separately qualifies canonical filesystem identity when present.
        return std::str::from_utf8(raw).ok()
            .is_some_and(|value| git_cli_path(Path::new(value)) == git_cli_path(expected));
    }
    #[cfg(not(windows))]
    { raw == expected.as_os_str().as_encoded_bytes() }
}

#[cfg(all(windows, test))]
#[test]
fn canonical_windows_git_cli_real_worktree_roundtrip() {
    let temp = tempfile::tempdir().unwrap();
    let root = fs::canonicalize(temp.path()).unwrap();
    let repo = root.join("source");
    let presentation = root.join("presentation");
    fs::create_dir(&repo).unwrap();
    fs::create_dir(&presentation).unwrap();
    let git = |args: &[&str]| {
        let output = workspace_git_command().arg("-C").arg(git_cli_path(&repo))
            .args(args).output().unwrap();
        assert!(output.status.success(), "{}", String::from_utf8_lossy(&output.stderr));
    };
    git(&["init", "-q"]);
    fs::write(repo.join("marker"), "native Git fixture").unwrap();
    git(&["add", "marker"]);
    git(&["-c", "user.name=Fixture", "-c", "user.email=fixture@local.invalid", "commit", "-qm", "seed"]);
    let cfg = UniversalExecutorConfig {
        store_root: root.join("store"),
        workspace_root: Some(presentation.clone()),
        workspace_uid: None, workspace_gid: None, runner_path: None,
        allowed_executable_roots: vec![root.clone()],
        max_runtime_ms: 60000, max_output_bytes: 1048576,
    };
    let id = "winpg-canonical-git";
    let target = cfg.workspace_path(id);
    let revision = resolve_git_commit(&repo, "HEAD").unwrap();
    let out = workspace_git_command().arg("-C").arg(git_cli_path(&repo))
        .args(["worktree","add","--detach"]).arg(git_cli_path(&target))
        .arg(&revision).output().unwrap();
    assert!(out.status.success(), "{}", String::from_utf8_lossy(&out.stderr));
    let actual = verified_interrupted_open(&repo,&target,&revision).unwrap();
    assert_eq!(actual, fs::canonicalize(&target).unwrap());
    fs::create_dir(&cfg.store_root).unwrap();
    create_workspace_private_git_snapshot(&cfg,id,&repo,&revision,&actual).unwrap();
    let private=cfg.workspace_private_git_path(id);
    assert!(!workspace_private_git_has_outputs(&private,&revision).unwrap());
    let inv=git_output_bytes(&repo,["worktree","list","--porcelain","-z"]).unwrap();
    assert!(inv.split(|b| *b==0).any(|v| v.strip_prefix(b"worktree ")
        .is_some_and(|path| git_registered_path_matches(path,&actual))));
    assert!(!git_registered_path_matches(b"C:/different", &actual));
    remove_git_worktree(&repo,&actual,false).unwrap();
    assert!(!target.exists());
    assert_eq!(resolve_git_commit(&repo,"HEAD").unwrap(),revision);
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
